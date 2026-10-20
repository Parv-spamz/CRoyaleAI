# Frozen descriptive gradient metrics

Two models,16 matched batches each,128 draws/batch=4096 model-row views; repeated
rows and mirrors are correlated. Sample schedule indices0,500,...,7500 only.
All original loss coefficients and labels are unchanged. Original scalar loss and
component values must match exactly. Finite gradients, unchanged model state and
empty parameter .grad are mandatory. No optimizer exists in the collector.

Save all five float32 gradient vectors, boolean per-tensor reachability and original
total vector. Summation consistency uses max error<=1e-5+1e-4*maxabs(total), plus
relative L2 error<=1e-4 (absolute1e-6 when total norm zero). This prospective fp32
autograd-linearity tolerance is diagnostic only and waives no historical gate.
Independent float64 norms/dots/cosines use rtol1e-10/atol1e-12 across reduction
orders; counts, membership, labels, hashes and reachability are exact.

For all parameters and separately the shared cell/other reachable subset report
five norms,5x5 dots/cosines,cell/rest norms/dot/cosine,cell/total dot and opposition
booleans. Zero-denominator cosines stay null. Report every batch and aggregate
counts/ranges per checkpoint; no seed/batch selection or numerical success floor.
No correction of metrics, loss weights, labels,1tile criterion or model verdict.
