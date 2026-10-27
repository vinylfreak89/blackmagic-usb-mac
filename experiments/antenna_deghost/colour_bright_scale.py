# the colour copy is measured against an assumed (standard) main burst, which lies outside the capture window, so its
# absolute size is not known; scan one real scale for the whole tape on the colour-predicted echo (phase and delay as
# predicted), on the same line-start check as colour_bright_check.py
import sys; sys.argv = sys.argv[:2]
exec(open('colour_bright_check.py').read().split("ms = res['sync'][4]")[0])
print('%-44s misfit per sample %7.2f' % ('no ghost', run('no ghost', lambda s: [], lambda s: [])))
for k in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7):
    run('colour-predicted echo x %.2f' % k, lambda s, k=k: [Tc], lambda s, k=k: [k * gA(s)[0]])
