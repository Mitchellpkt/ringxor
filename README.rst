=========================
Transaction tree analysis
=========================

Mitchell P. Krawiec-Thayer (@isthmus) // Noncesense Research Lab

This library enables passive deanonymization of Monero-style blockchains for true spends revealed by "differ-by-one" ring pair analysis (described below). The analysis engine leverages CPU multiprocessing and automatically distributes the workload across cores (this can be disabled & the number of workers can be adjusted).

**NOTE: If you generate transactions with a "wallet2"-based software (such as the core GUI or CLI) then they should not exhibit the anomaly exploited by this analysis.**

**NOTE: This is under early-stage development, and the API is likely to change frequently and dramatically.**

Introduction to differ-by-one (DBO) analysis
============================================
Suppose we have the sets ``{2, 4, 8}`` and ``{2, 4, 10}``. We'll say that this pair has a "differ by one" (DBO) relationship, because singleton 8 sticks out on the left, and the singleton 10 sticks out on the right.

Any pair of rings whose members differ by only one element will be called a "DBO ring pair". We'll refer to any ring that belongs to any DBO pair as a "DBO ring". (Note that one DBO ring can be in many DBO pairs, and this is disturbingly common on the Monero blockchain)

Each DBO ring produces one new singleton, corresponding to the output spent in that ring. From a graph analysis perspective, this reveals one edge of the transaction tree belonging to the subgraph representing the true flow of funds. We can record this edge as a ``(ring, output)`` tuple. Since key images are 1:1 with rings, it also works as well to record ``(key image, output)`` tuple. Any time that output shows up in a different ring signature, we know that it is a decoy and can remove its possible spend from the set of plausible edges.

Example output
==============

(below is an excerpt of real results from the Monero blockchain)::

    Txn: 48ab24a942778d0c7d79d8bbc7076329ae45b9b7c8cc7c15d105e135b4746587
    Key Image: f7c4e158caaa3d8b15bbf878ed15392d99debf1eaf78a421637fd13e51dce229
    Spends output: 9641bf77a6f7031b1f077c183e590b3e0c6cf9acd951aa9436d4b670958aff53

    Txn: 71879ba6099ea18d456cd31694b0860f3649ebeb28ce5630ccb1be312c0cc8cb
    Key Image: 8b4afa486c7a8d40c569a172a5ea2200e36c921ee543c2a6c7e43452c3efc9bd
    Spends output: c75a7b36d2311ce6b41ad062133a0a4b1f16c21d3251c10719158330d4799f7a

    Txn: 48ab24a942778d0c7d79d8bbc7076329ae45b9b7c8cc7c15d105e135b4746587
    Key Image: f37df1f2d6e28ef4fd2a22fa4172aa5453e5dad54e44503e130ce18ef4a28df9
    Spends output: c419117a83906e84c76de0604b85c00888097c1993b05784f3efdd84633e6d77

    Txn: 71879ba6099ea18d456cd31694b0860f3649ebeb28ce5630ccb1be312c0cc8cb
    Key Image: 71f9ad1b7735bad5d0f26eb9ea23545af1a39517e0e184c7c74d4ee9203156c1
    Spends output: 736eb676e8dcf030ab4116afe4c8c14e37adff19de70fd25e092a5da20dac778

DBO pairs observed in the wild
=======================================

There are multiple contexts in which DBO pairs found in the wild on Monero.


intERtransaction DBO pairs
--------------------------
We can have DBO ring pairs across different transactions, for example:

+ https://xmrchain.net/tx/6fb06bcd042e5f705a458a37cc3aaf6a1ad7a35657cf03f74e3aea383a47fb7e
+ https://xmrchain.net/tx/4509d22833ca47ec224fcd226626bc830056d39a6ff1278c56a4796645c47859

Here is another more extreme example, with dozens of DBO ring pairs across just two many-input transactions:

+ https://xmrchain.net/tx/71879ba6099ea18d456cd31694b0860f3649ebeb28ce5630ccb1be312c0cc8cb
+ https://xmrchain.net/tx/48ab24a942778d0c7d79d8bbc7076329ae45b9b7c8cc7c15d105e135b4746587

*(as an aside, there are many oddities in the above pair, such as the incorrect decoy selection algorithm for most of the rings (old clusters, and then one new output), and the fact that the 4th ring does appear to be sampled from the correct distribution?)*

intRAtransaction DBO pairs
--------------------------
We also find many examples of DBO ring pairs within the same transaction, for example:

* Mitchell TODO: dig up one of those old links for this

Scope = everything
------------------
By optionally removing transaction labels we can automatically detect intertransaction and intratransaction DBO relationships in a single pass.

Scalability
===========

If ``R`` is the number of rings on the blockchain, to make each pairwise comparison we would naively expect to do ``R^2`` checks

However, we do not need to check along the diagonal of the matrix, because a ring cannot be a DBO ring pair with itself. So we can reduce the number of checks to ``R^2 - R``

Furthermore, because ring xor is symmetric, we only need to look at the upper triangle of the matrix! This brings us down to ``(R^2 - R) / 2`` checks.

Also, because sets with different sizes cannot produce a DBO ring pair, we can reduce the number of checks by only comparing rings of the same size. So consider the set of rings sized 11 (``R11``) and the set of ring sized 16 (``R16``). We only need to check ``(R11^2 - R11 + R16^2 - R16) / 2`` which is much less than ``(R^2 - R) / 2``

This process is "embarrassingly parallel", and this library implements CPU multiprocessing.

Benchmarks for new unoptimized python code: about 850,000 ring pair checks per second. Previous prototype code clocked in an order of magnitude faster, but I think the new numbers are more practical when actually juggling a large number of rings.

Future work - converting from ``O(R^2)`` to ``O(R)``
====================================================

While the naive algorithm scales with ``O(R^2)`` with respect to number of rings, **applying preliminary sorting enables exact matching to be subsequently executed in effectively** ``O(R)`` **time!!**

This is achieved by sorting the outputs within each ring (usually this is already the case) and then applying a lexicographic sort to the rings themselves. Then checks are made based on the first 3 elements of each ring (note: this will always be exactly the first 3 regardless of the ring size).

(1) When comparing two rings A & B, we only need to check the symmetric difference of the first 3 elements of each ring. For example the symmetric difference of `{1,2,3}` and `{2,3,4}` would be `{1,4}`. If the difference has <= 2 elements, process the entirety of both rings to check if they are DBO. If there are >2 differences among the first 3 elements, there is no need to check the entire ring.

(2) If there are >=4 differences among the first 3 elements, we have exited the neighborhood of possible DBO matches for ring A, and can step forward to the next candidate.

Example: Consider several rings, which we have sorted lexicographically (both inside the rings, and the rings themselves)::

    A = {0, 1, 2, 3, 4}
    B = {2, 4, 6, 7, 8}
    C = {4, 6, 7, 8, 9}

First we check A[:3] and B[:3]. Since {0,1,2} and {2,4,6} have a symmetric difference with 4 elements ({0,1,4,6}) we can skip the rest of the calculation. Furthermore we skip all further comparisons with A. **(This type of early break is the main optimization breakthrough that helps us avoid O(R^2) complexity!!)**

Now we check B[:3] and C[:3]. Since {2,4,6} and {4,6,7} have a symmetric difference of length 2 we must check the entire rings to see if they are DBO. (In this case, they are DBO, so we can infer that ring B spends output #2 and ring C spends output #9)