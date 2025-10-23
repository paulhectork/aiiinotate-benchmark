# OUTTAKES FROM THE BENCHMARK

## General

- aiiinotate handles concurrent clients quite well: benchmark was done by inserting data in 20 simultanenous threads.

## Insert

- **insert manifests**: number of manifests has a big impact on performance: going from 1000 manifests to 10000 manifests causes the performance to drop from `~30it/s` to `~3-5it/s`. **à vérifier**

## Delete

- **mass deleting documents is slow on very large collections**:
    - noticed when doing `Benchmark.purge` (which deleted all annotations on manifests using parrallelized HTTP queries to routes of the annotation server) with 1.000 manifests, 10.000 canvases/manifest, 100.000.000 annotations: +1h to delete all 100M annotations
    - explanation: 
        - mongo locks the database from start of a delete query until the query is completed. If the delete filter is not done on an index field, what happens in a *collection scan*: every single document is successively read from disk.
        - [see this explanation](https://stackoverflow.com/a/33164008)
        - when running a long delete, open `mongosh` and run `db.currentOp({ op: "remove" })`. find the delete operation, and you'll see `planSummary: 'COLLSCAN'`.
    - consequences:
        - 1h+ to delete 100.000.000 annotations, `htop`: CPU 200%, memory 50%
        - when deleting 100.000.000 annotations, 
        - multithreading is *probably* ineffective on delete when working with very large collections: if I understand correctly, all threads are blocked except from the one currently doing the delete.
    - workarounds:
        - index fields to be deleted
        - run the deletion directly through a mongosh command => **this is what is done in `AiiinotateAdapter.purge()`**
