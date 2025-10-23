# OUTTAKES FROM THE BENCHMARK

## General

- aiiinotate handles concurrent clients quite well: benchmark was done by inserting data in 20 simultanenous threads.

## Insert

- insert manifests: number of manifests has a big impact on performance: going from 1000 manifests to 10000 manifests causes the performance to drop from `~30it/s` to `~3-5it/s`. **à vérifier**
-

