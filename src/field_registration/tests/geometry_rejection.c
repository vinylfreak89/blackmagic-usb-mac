/* Pure energy fixtures and state transitions; no source-labelled tuning. */
#include "../geometry_engine.c"
#include <assert.h>
#include <stdio.h>

static ge_comb_result comb(void) {
    ge_comb_result c={.shift=0,.margin=1,.decided=0};
    for(int i=0;i<11;i++)c.energies[i]=10;
    c.energies[5]=c.energies[6]=1;
    return c;
}
static geometry_engine seeded(void) {
    geometry_engine g={.held=2,.provisional=1,.basis_valid=1,
        .have_placement=1,.last_d=-1,.last_d2=3,.basis_first={24,286}};
    return g;
}
int main(void) {
    ge_comb_result c=comb(),saved=c;
    ge_comb_evidence e=ge_comb_examine(&c,-1);
    assert(e.ratio==10 && e.floor_lo==0 && e.floor_hi==1 && e.basin);
    assert(e.rise_left==10 && e.rise_right==10 && !memcmp(&c,&saved,sizeof c));
    c.energies[7]=1.5;e=ge_comb_examine(&c,8);
    assert(e.floor_hi==2 && e.basin && isnan(e.ratio)); // inclusive floor; no fabricated energy
    c.energies[8]=1.6;c.energies[9]=1; // disconnected low point is NOT part of the floor
    e=ge_comb_examine(&c,0);assert(e.floor_hi==2 && e.basin && e.rise_right==1.6);
    c=comb();for(int i=7;i<11;i++)c.energies[i]=1.1;
    e=ge_comb_examine(&c,-1);assert(!e.basin && e.floor_hi==5 && isnan(e.rise_right));
    c=comb();c.shift=-5;c.energies[0]=.9;
    e=ge_comb_examine(&c,0);assert(!e.basin && e.floor_lo==-5 && isnan(e.rise_left));
    c=comb();c.energies[5]=c.energies[6]=0;
    e=ge_comb_examine(&c,0);assert(e.ratio==1 && e.basin && isinf(e.rise_left));
    e=ge_comb_examine(&c,-1);assert(isinf(e.ratio));
    memset(c.energies,0,sizeof c.energies);e=ge_comb_examine(&c,-1);
    assert(e.ratio==1 && !e.basin && e.floor_lo==-5 && e.floor_hi==5);
    c.margin=NAN;e=ge_comb_examine(&c,0);assert(isnan(e.ratio) && !e.basin);

    for(int audit_only=0;audit_only<2;audit_only++) {
        geometry_engine g=seeded(),before=g;
        ge_decision o={.comb=comb(),.comb_ran=!audit_only};int d=-1,d2=4;
        reject_placement(&g,&o,&d,&d2);
        if(audit_only)assert(!o.rejected && d==-1 && d2==4 && !memcmp(&g,&before,sizeof g));
        else {
            assert(o.rejected && !o.discarded && o.refused_d==-1 && o.substituted_d==0);
            assert(d==0 && d2==4 && !g.held && !g.provisional && !g.basis_valid);
            assert(!g.basis_first[0] && !g.basis_first[1] && !o.comb.decided);
            assert(o.relative_source==GE_SOURCE_REJECT);
        }
    }
    geometry_engine g=seeded();ge_decision o={.comb=comb(),.comb_ran=1};int d=-1,d2=4;
    o.comb.energies[4]=2;reject_placement(&g,&o,&d,&d2);
    assert(!o.rejected && g.held==2 && d==-1); // strictly greater, not >=
    o.comb.energies[4]=nextafter(2,INFINITY);reject_placement(&g,&o,&d,&d2);
    assert(o.rejected && d==0);
    for(int have=0;have<2;have++) {
        g=seeded();g.have_placement=have;o=(ge_decision){.comb=comb(),.comb_ran=1};
        for(int i=7;i<11;i++)o.comb.energies[i]=1.1;
        d=-2;d2=4;reject_placement(&g,&o,&d,&d2);
        assert(o.rejected && o.discarded && o.refused_d==-2 && !g.held && !g.basis_valid);
        assert(d==(have?-1:0) && d2==(have?3:0)); // whole previous pair, not new anchor
        assert(o.anchor_source==(have?GE_SOURCE_DISCARD_PREVIOUS:GE_SOURCE_DISCARD_START));
    }
    g=seeded();o=(ge_decision){.comb=comb(),.comb_ran=1};d=7;d2=2;
    reject_placement(&g,&o,&d,&d2);assert(isnan(o.rejection.ratio) && !o.rejected && d==7);
    puts("GEOMETRY-REJECTION PASS: tied floor, walls, exact bars, zero energy, missing search, audit, substitution, discard pair, reset basis");
}
