/* Private, source-qualified box verdict instrument, not box geometry.
 * Measured basis and deliberately limited scope: tests/BOX_EXCLUSION.md.
 * This header is included by field_registration.c, not a separate API. */
static double box_median(double *v,int n)
{
    /* Insertion sort over at most 240 row statistics; no allocation. */
    for(int i=1;i<n;++i){double a=v[i];int j=i;while(j && v[j-1]>a){v[j]=v[j-1];--j;}v[j]=a;}
    return (v[(n-1)/2]+v[n/2])/2;
}
static double box_hist_median(const unsigned hist[256],unsigned n)
{
    unsigned count=0;int a=-1,b=-1;
    for(int k=0;k<256;++k){count+=hist[k];if(a<0 && count>(n-1)/2)a=k;if(count>n/2){b=k;break;}}
    return ((double)a+b)/2;
}
static double box_row_structure(const uint8_t *line)
{
    /* 24..695 is the measured harness/comb aperture, not a porch claim.
     * 256 histogram entries are the complete 8-bit sample alphabet. */
    unsigned hist[256]={0},diff[256]={0},sum=0;
    for(int x=24;x<696;++x){int y=line[2*x+1];++hist[y];sum+=(unsigned)y;
        if(x>24){int d=y-line[2*(x-1)+1];++diff[abs(d)];}}
    const double mean=(double)sum/(696-24);
    const double noise=box_hist_median(diff,696-24-1);
    /* Merge sample values outwards from their mean to rank absolute
     * deviations exactly, without quantizing the mean or allocating. */
    int lo=(int)floor(mean),hi=lo+1;unsigned count=0;
    double a=-1,b=-1;
    while(lo>=0 || hi<256){
        bool left=lo>=0 && (hi>=256 || mean-lo<=hi-mean);
        int k=left?lo--:hi++;double d=fabs(k-mean);count+=hist[k];
        if(a<0 && count>(696-24-1)/2)a=d;
        if(count>(696-24)/2){b=d;break;}
    }
    const double spread=(a+b)/2;
    /* A zero denominator is unmeasurable unless the row is exactly flat.
     * Do not substitute a typed noise floor. */
    return noise>0?spread/noise:(spread==0?0:-1);
}
static bool observe_box(const uint8_t *raster,int field,int recorded_last)
{
    /* These are FITTED instrument limits, explicitly not source minima.
     * 3 rejects the card's measured two-row backdrop step. 6 and 40 bound
     * the harness's tested band/content class. 0.28 lies between measured
     * band 0.19..0.20 and WARNING 0.39..0.41 of structured level.
     * A negative verdict does not establish unboxed/full-picture geometry. */
    enum { MIN_BAND=6, MIN_CONTENT=40, STRUCTURED_RUN=3 };
    const int first=field?FIELDREG_FIELD2_START:FIELDREG_FIELD1_START;
    int n=recorded_last-first+1;
    if(n>FIELDREG_FIELD_LINES)n=FIELDREG_FIELD_LINES;
    if(n<MIN_CONTENT+2*MIN_BAND)return false;
    double h[FIELDREG_FIELD_LINES],v[FIELDREG_FIELD_LINES];
    for(int y=0;y<n;++y){h[y]=box_row_structure(raster+(size_t)(first+y)*FIELDREG_BYTES_PER_LINE);if(h[y]<0)return false;}
    /* Middle third is this instrument's reference aperture, not a claim
     * that every legitimate source has content there. */
    int size=0;for(int y=n/3;y<2*n/3;++y)v[size++]=h[y];
    double level=box_median(v,size),cut=0.28*level;
    if(level<=0 || h[0]>=cut)return false;
    int run=0,content=-1;
    for(int y=0;y<n;++y){run=h[y]>=cut?run+1:0;if(run==STRUCTURED_RUN){content=y+1-run;break;}}
    if(content<MIN_BAND)return false;
    int structured=0;run=0;
    for(int y=content;y<n;++y){
        if(h[y]>=cut){++structured;run=0;}else ++run;
        if(run<MIN_BAND || structured<MIN_CONTENT)continue;
        const int begin=y+1-run;
        /* The lower candidate extends to the recorded edge. Its median
         * may tolerate terminal switch rows; no switch endpoint is used.
         * This is a categorical verdict, never a reported band extent. */
        size=0;for(int j=begin;j<n;++j)v[size++]=h[j];
        if(box_median(v,size)<cut)return true;
    }
    return false;
}
