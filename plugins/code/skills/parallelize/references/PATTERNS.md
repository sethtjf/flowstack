# Concurrency patterns by language

Each section gives the idiom for independent calls, for a bounded loop, and the pitfalls that turn a safe-looking change into a bug. Prefer a helper the repo already has over any of these.

## JavaScript and TypeScript

Independent calls, fail-fast (matches sequential `await` error behavior):

```ts
const [user, orders] = await Promise.all([getUser(id), getOrders(id)]);
```

Start early, await late:

```ts
const ordersP = getOrders(id);      // starts now
const user = await getUser(id);
const flags = computeFlags(user);   // CPU work overlaps the orders call
const orders = await ordersP;
```

Bounded loop, order kept:

```ts
import pLimit from "p-limit";
const limit = pLimit(8);
const items = await Promise.all(ids.map((id) => limit(() => load(id))));
```

Pitfalls:

- `Promise.all` rejects on the first failure but the other promises keep running. If they write, or hold resources, pass an `AbortSignal` and abort on failure.
- A promise created early and awaited late can reject while unobserved, causing an `unhandledRejection` crash in Node if the code between start and await throws first. Attach handling or keep the window short and free of throws.
- `Promise.allSettled` swallows errors that used to throw. Use it only when the old code caught each call individually.
- `forEach(async ...)` does not await anything. Replacing it with `Promise.all` changes behavior from fire-and-forget to awaited; confirm which was intended.
- Prisma `$transaction(async (tx) => ...)`: queries on `tx` run on one connection; parallel calls on `tx` serialize or error. The array form `$transaction([...])` is already batched.
- `pg` `Client` (not `Pool`) runs one query at a time.

## Python (asyncio)

Independent calls:

```python
async with asyncio.TaskGroup() as tg:     # 3.11+, cancels siblings on failure
    user_t = tg.create_task(get_user(id))
    orders_t = tg.create_task(get_orders(id))
user, orders = user_t.result(), orders_t.result()
```

On 3.10 and earlier, `asyncio.gather(a(), b())` is fail-fast but does not cancel the siblings.

Bounded loop, order kept:

```python
sem = asyncio.Semaphore(8)
async def one(i):
    async with sem:
        return await load(i)
items = await asyncio.gather(*(one(i) for i in ids))
```

Pitfalls:

- `TaskGroup` raises an `ExceptionGroup`, not the original exception. Callers catching a specific exception type need `except*` or an unwrap, or the error contract changes.
- SQLAlchemy `AsyncSession` and a single `asyncpg` connection are not safe for concurrent use. Use separate sessions from the pool or keep it sequential.
- `contextvars` copy into tasks at creation; later changes in the parent are not seen by running tasks.
- Sync code (`requests`, Django ORM) gains nothing from `asyncio`. Use a thread pool (`concurrent.futures.ThreadPoolExecutor`) for independent blocking calls, and respect Django's per-thread connections.

## Go

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(8)
results := make([]Item, len(ids))
for i, id := range ids {
    g.Go(func() error {           // Go 1.22+ loop vars are per-iteration
        item, err := load(ctx, id)
        results[i] = item         // index write, no shared append
        return err
    })
}
if err := g.Wait(); err != nil { return err }
```

Pitfalls:

- Pass the errgroup's `ctx` so siblings cancel on the first error.
- Before Go 1.22, capture `i` and `id` in the loop body.
- `append` to a shared slice or writes to a map from goroutines race. Write by index or guard with a mutex.
- `database/sql` `*sql.Tx` is one connection; do not use it from several goroutines.

## Rust (Tokio)

```rust
let (user, orders) = tokio::try_join!(get_user(id), get_orders(id))?;
```

Bounded loop, order kept:

```rust
use futures::{stream, StreamExt, TryStreamExt};
let items: Vec<_> = stream::iter(ids)
    .map(|id| load(id))
    .buffered(8)               // buffer_unordered loses input order
    .try_collect()
    .await?;
```

Pitfalls:

- `try_join!` runs futures concurrently on one task, not in parallel threads; that is right for I/O. Use `tokio::spawn` or `JoinSet` only when you need parallel CPU or `'static` tasks.
- A `&mut` borrow of a connection or transaction cannot be shared across futures; the borrow checker usually catches it, so do not work around it with `Arc<Mutex<_>>` around a transaction.

## Java and Kotlin

Java:

```java
var userF = CompletableFuture.supplyAsync(() -> users.get(id), ioExecutor);
var ordersF = CompletableFuture.supplyAsync(() -> orders.get(id), ioExecutor);
CompletableFuture.allOf(userF, ordersF).join();
```

Pass an explicit executor; the default common pool is sized for CPU work. On Java 21+, a virtual-thread executor or structured concurrency (preview) are alternatives. `join()` wraps failures in `CompletionException`, so unwrap where callers catch specific types.

Kotlin coroutines:

```kotlin
coroutineScope {
    val user = async { getUser(id) }
    val orders = async { getOrders(id) }
    render(user.await(), orders.await())
}
```

Bound loops with a `Semaphore(8)` and `withPermit`. A JDBC `Connection` or JPA `EntityManager` is not safe across threads.

## C#

```csharp
var userTask = GetUserAsync(id);
var ordersTask = GetOrdersAsync(id);
await Task.WhenAll(userTask, ordersTask);
var (user, orders) = (userTask.Result, ordersTask.Result);
```

Bound loops with `Parallel.ForEachAsync(ids, new ParallelOptions { MaxDegreeOfParallelism = 8 }, ...)` or a `SemaphoreSlim`. An EF Core `DbContext` does not support concurrent operations; use separate contexts from a factory or stay sequential. `await Task.WhenAll` rethrows only the first exception.

## Choosing a concurrency limit

Start from the smallest of: the connection pool size minus headroom for other requests, the downstream rate limit divided by expected concurrent requests, and 8 to 16 for unknown HTTP APIs. State the number and the reason in the report. If the repo has a configured limit or client-side rate limiter, use it.
