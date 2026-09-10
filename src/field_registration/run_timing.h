/* Independent, deliberately qualified run observation. No phase-envelope
 * disjointness test and no 64/200 limits. A long black rectangle alone is NOT
 * a timing observation: both locally readable porches must depart too.
 * Limits and falsification controls: tests/RUN_TIMING.md. */
typedef struct run_profile {
    int left,right,start,length,runs;
    unsigned porch_hist[256],run_hist[256];
} run_profile;

static run_profile timing_run(const uint8_t *line,const unsigned *blank)
{
    run_profile p={.start=-1};
    while(p.left<H_SAMPLES && blank[line[2*p.left+1]])++p.left;
    while(p.right<H_SAMPLES-p.left && blank[line[2*(H_SAMPLES-1-p.right)+1]])++p.right;
    for(int x=0;x<p.left;++x)++p.porch_hist[line[2*x+1]];
    for(int x=H_SAMPLES-p.right;x<H_SAMPLES;++x)++p.porch_hist[line[2*x+1]];
    /* Full interior runs only; an edge-connected dark region does not expose
     * both endpoints of relocated blanking. All-flat rows supply no phase. */
    for(int x=p.left;x<H_SAMPLES-p.right;) {
        if(!blank[line[2*x+1]]) {++x;continue;}
        int start=x;while(x<H_SAMPLES-p.right && blank[line[2*x+1]])++x;
        int n=x-start;
        if(n>=H_BLANK) {
            ++p.runs;
            if(n>p.length) {p.start=start;p.length=n;}
        }
    }
    if(p.start>=0)for(int x=p.start;x<p.start+p.length;++x)++p.run_hist[line[2*x+1]];
    return p;
}

static bool normal_porch(const run_profile *p)
{
    /* The standards supply total overlap, NOT unconditional left/right
     * labels. This instrument requires both ends readable locally; sources
     * showing blanking at only one end are outside its qualification. */
    return p->left>0 && p->right>0 && p->left+p->right>=H_OVERLAP &&
           p->left+p->right<H_BLANK;
}

static void measure_run_switch(const uint8_t *raster,int field,field_measurement *m)
{
    unsigned blank[256]={0};
    for(int r=field?270:7;r<=(field?278:15);++r)
        for(int x=0;x<H_SAMPLES;++x)++blank[raster[(size_t)r*FIELDREG_BYTES_PER_LINE+2*x+1]];
    /* Generated blanking supplies the observed code alphabet only, not a
     * static-picture tolerance. Distribution agreement below uses the source's
     * locally readable porches. References exist for this invocation only. */
    run_profile history[H_HISTORY]={0},previous={0};
    unsigned count=0,next=0;
    int t=-1,s=-1,run_start=-1,run_length=-1;
    double distance=-1,tolerance=-1;
    int held_left=0,held_right=0;
    for(int row=m->top;row<=m->recorded_last;++row) {
        run_profile p=timing_run(raster+(size_t)row*FIELDREG_BYTES_PER_LINE,blank);
        if(t>=0 && normal_porch(&p) && p.left>=held_left && p.right>=held_right)
            t=s=-1;
        int left=H_SAMPLES,right=H_SAMPLES;
        unsigned histogram[256]={0},samples=0;
        bool basis=false;
        for(unsigned i=0;i<count;++i)if(normal_porch(&history[i])) {
            basis=true;
            if(history[i].left<left)left=history[i].left;
            if(history[i].right<right)right=history[i].right;
            for(int k=0;k<256;++k) {histogram[k]+=history[i].porch_hist[k];samples+=history[i].porch_hist[k];}
        }
        /* A shortened but surviving leading porch is not a FULL other-head
         * row. This qualified orientation needs its complete disappearance,
         * plus loss of the locally observed trailing extent. */
        bool full=basis && p.runs==1 && p.left==0 && p.right<right;
        bool prior_normal=basis && normal_porch(&previous) && previous.left>=left && previous.right>=right;
        bool prior_partial=basis && !normal_porch(&previous) &&
            previous.left>=left && previous.right<right;
        /* Do not relabel a later readable row S if the preceding row already
         * lost both porches but its interval was obscured or incomplete. */
        if(full && (prior_normal || prior_partial)) {
            bool compatible=true;unsigned a=0,b=0;double delta=0;
            for(int k=0;k<256;++k) {
                if(p.run_hist[k] && !histogram[k])compatible=false;
                a+=p.run_hist[k];b+=histogram[k];
                double d=fabs((double)a/p.length-(double)b/samples);
                if(d>delta)delta=d;
            }
            /* Derive the allowed CDF variation from these source porches:
             * greatest per-row distance from their pooled distribution.
             * This is observed variation, not a confidence probability, and
             * equal distribution still cannot identify black content alone. */
            double envelope=0;
            for(unsigned i=0;i<count;++i)if(normal_porch(&history[i])) {
                unsigned c=0,d=0,n=(unsigned)(history[i].left+history[i].right);
                for(int k=0;k<256;++k) {
                    c+=history[i].porch_hist[k];d+=histogram[k];
                    double gap=fabs((double)c/n-(double)d/samples);
                    if(gap>envelope)envelope=gap;
                }
            }
            if(compatible && delta<=envelope) {
                t=prior_partial?row-1:row;s=row;
                run_start=p.start;run_length=p.length;distance=delta;tolerance=envelope;
                held_left=left;held_right=right;
            }
        }
        history[next]=previous;previous=p;
        next=(next+1)%H_HISTORY;if(count<H_HISTORY)++count;
    }
    if(t>=0) {
        fieldreg_switch_observations *o=&m->switch_observations;
        o->run_t=(int16_t)t;o->run_s=(int16_t)s;
        o->run_start=(int16_t)run_start;o->run_length=(int16_t)run_length;
        o->run_blank_distance=distance;
        o->run_blank_tolerance=tolerance;
    }
}
