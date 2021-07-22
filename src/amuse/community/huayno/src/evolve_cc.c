/*
 * The Connected Components Hamiltonian split uses a connected component search
 * on the time step graph of the system to find isolated subsystems with fast
 * interactions. These subsystems are then evolved at greater accuracy compared
 * to the rest system.
 * Equation numbers in comments refer to: J\"anes, Pelupessy, Portegies Zwart, A&A 2014 (doi:10.1051/0004-6361/201423831)
 */

#include <tgmath.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#include <string.h>

#include "evolve.h"
#include "evolve_kepler.h"
#include "evolve_bs.h"

// this is a bit weird, why not use NULL pointer?
#define IS_ZEROSYS(SYS) (((SYS)->n == 0) && \
                         ((SYS)->nzero == 0) && \
                         ((SYS)->part == NULL) && \
                         ((SYS)->last == NULL) && \
                         ((SYS)->next_cc == NULL) && \
                         ((SYS)->zeropart == NULL) && \
                         ((SYS)->lastzero == NULL) )

#define IS_ZEROSYSs(SYS) IS_ZEROSYS(&(SYS))

#define LOG_CC_SPLIT(C, R) \
{ \
  LOG("clevel = %d s.n = %d c.n = {", clevel, s.n); \
  for (struct sys *_ci = (C); !IS_ZEROSYS(_ci); _ci = _ci->next_cc) printf(" %d ", _ci->n ); \
  printf("} r.n = %d\n", (R)->n); \
};

#define PRINTSYS(s) \
{ \
  LOG("sys %d %d : {",s.n,s.nzero); \
  for (UINT i=0;i<s.n-s.nzero;i++) printf(" %d", GETPART(s, i)->id); printf(" | "); \
  for (UINT i=s.n-s.nzero;i<s.n;i++) printf(" %d", GETPART(s, i)->id); printf(" }\n"); \
};

#define PRINTOFFSETS(s) \
{ \
  LOG("sysoffsets %d %d : {",s.n,s.nzero); \
  for (UINT i=0;i<s.n-s.nzero;i++) printf(" %d", GETPART(s, i)-s.part); printf(" | "); \
  for (UINT i=s.n-s.nzero;i<s.n;i++) printf(" %d", GETPART(s, i)-s.part); printf(" }\n"); \
};


#define LOGSYS_ID(SYS) for (UINT i = 0; i < (SYS).n; i++) { printf("%u ", (SYS).part[i].id); } printf("\n");
#define LOGSYSp_ID(SYS) for (UINT i = 0; i < (SYS)->n; i++) { printf("%u ", (SYS)->part[i].id); } printf("\n");
#define LOGSYSC_ID(SYS) for (struct sys *_ci = &(SYS); !IS_ZEROSYS(_ci); _ci = _ci->next_cc) {printf("{"); for (UINT i = 0; i < _ci->n; i++) {printf("%u ", _ci->part[i].id); } printf("}\t");} printf("\n");

void split_cc_old(int clevel,struct sys s, struct sys *c, struct sys *r, DOUBLE dt) {
  /*
   * split_cc: run a connected component search on sys s with threshold dt,
   * creates a singly-linked list of connected components c and a rest system r
   * c or r is set to zerosys if no connected components/rest is found
   */
  int dir=SIGN(dt);
  dt=fabs(dt);
  diag->tstep[clevel]++; // not directly comparable to corresponding SF-split statistics
  struct sys *c_next;
  if(s.n<=1) ENDRUN("This does not look right...");
  if(s.nzero>0 && s.n!=s.nzero && s.zeropart!=s.last+1) 
    ENDRUN("split_cc only works on contiguous systems");
  c_next = c;
  *c_next = zerosys;
  UINT processed = 0; // increase if something is added from the stack to the cc
  struct particle *comp_next = s.part; // increase to move a particle from stack to cc; points to the first element of the stack
  UINT comp_size = 0; // amount of particles added to the current cc
  struct particle *stack_next = comp_next+1; // swap this with s[i] to increase the stack
  UINT stack_size = 1; // first element of the stack is comp_next
                       // last element of the stack is comp_next + stack_size - 1 == stack_next-1
  struct particle *rest_next = GETPART(s, s.n-1); // swap this to add to the rest-system
  // find connected components
  while (processed < s.n)
  {
    //LOG("split_cc: searching for connected components: %d / %d\n", processed, s.n);
    // search for the next connected component
    while (stack_size > 0)
    {
      // iterate over all unvisited elements
      for (struct particle *i = stack_next; i <= rest_next; i++)
      {
        // if element is connected to the first element of the stack
        DOUBLE timestep = (DOUBLE) timestep_ij(comp_next, i,dir);
        diag->tcount[clevel]++;
        if ( timestep <= dt)
        {
          // add i to the end of the stack by swapping stack_next and i
          SWAP( *stack_next , *i, struct particle );
          stack_next++;
          stack_size++;
        }
      }
      // pop the stack; add to the connected component
      comp_size++;
      comp_next++;
      stack_size--;
    }
    processed += comp_size;
    // new component is non-trivial: create a new sys
    if (comp_size > 1)
    {
      //LOG("split_cc: found component with size: %d\n", comp_size);
      // create new component c from u[0] to u[cc_visited - 1]
      // remove components from u (u.n, u.part)
      c_next->n = comp_size;
      c_next->part = comp_next - comp_size;
      c_next->last = comp_next-1;
      c_next->next_cc = (struct sys*) malloc( sizeof(struct sys) );
      c_next = c_next->next_cc;
      *c_next = zerosys;
      if(stack_next!=comp_next) ENDRUN("consistency error in split_cc")
      // comp_next = stack_next; // should be unchanged
      comp_size = 0;
      stack_next= comp_next+1;
      stack_size = 1;
    // new component is trivial: add to rest
    }
    else
    {
      //LOG("found trivial component; adding to rest\n");
      SWAP( *(comp_next - 1), *rest_next, struct particle );
      rest_next--;
      comp_next = comp_next - 1;
      comp_size = 0;
      if(stack_next!=comp_next+1) ENDRUN("consistency error in split_cc")
      //stack_next = comp_next + 1; // should be unchanged
      stack_size = 1;
    }
  }
  if (processed != s.n)
  {
    ENDRUN("split_cc particle count mismatch: processed=%u s.n=%u r->n=%u\n", processed, s.n, r->n);
  }
  // create the rest system
  r->n = GETPART(s, s.n-1) - rest_next;
  if (r->n > 0)
  {
    r->part = rest_next+1;
    r->last = GETPART(s, s.n-1);
  }
  else
  {
    r->part = NULL;
    r->last = NULL;
  }
  //LOG("split_cc: rest system size: %d\n", r->n);
}

void split_cc(int clevel,struct sys s, struct sys *c, struct sys *r, DOUBLE dt) {
  /*
   * split_cc: run a connected component search on sys s with threshold dt,
   * creates a singly-linked list of connected components c and a rest system r
   * c or r is set to zerosys if no connected components/rest is found
   */
  int dir=SIGN(dt);
  dt=fabs(dt);
  diag->tstep[clevel]++; // not directly comparable to corresponding SF-split statistics
  struct sys *c_next;
  if(s.n<=1) ENDRUN("This does not look right...");
  c_next = c;
  UINT processed = 0; // increase if something is added from the stack to the cc
  struct particle **active, *comp_next, *compzero_next; // current active particle, and next in the mass and massless part 
  UINT comp_size, compzero_size;
  struct particle *stack_next=NULL, *stackzero_next=NULL; // two pointers keeping track of stack in massive and massless part 
  UINT stack_size, stackzero_size; //  counter for total size of stack and zero 
  struct particle *rest_next=NULL, *restzero_next=NULL; // swap this to add to the rest-system
  // find connected components
  
  if(s.n-s.nzero>0) stack_next=s.part;
  if(s.n-s.nzero>0) rest_next=s.last;
  if(s.nzero>0) stackzero_next=s.zeropart;
  if(s.nzero>0) restzero_next=s.lastzero;
  comp_next=stack_next;
  compzero_next=stackzero_next;
  *c_next=zerosys;     // initialize c_next 

  while (processed < s.n)
  {
    if(stack_next!=comp_next) ENDRUN("consistency error in split_cc\n")
    if(stackzero_next!=compzero_next) ENDRUN("consistency error in split_cc\n")
    //~ if(stack_next==rest_next && stackzero_next==restzero_next) ENDRUN("impossible")

    // startup stack 

    comp_size=0;
    compzero_size=0;
    if(stack_next!=NULL && stack_next<rest_next+1)
    {
      //~ LOG("stack_next init\n");
      stack_next++;
      stack_size=1;
    } 
    if(comp_next==stack_next && stackzero_next!=NULL  && stackzero_next<restzero_next+1)
    {
      //~ LOG("stackzero_next init\n");
      stackzero_next++;
      stack_size=1;
    } 
    if(stack_next==comp_next && stackzero_next==compzero_next) ENDRUN("impossible")
    
    // search for the next connected component
    while (stack_size > 0)
    {
      //~ LOG("stack_size %d\n", stack_size);
      active=NULL;
      if(stack_next!=NULL &&
         stack_next-comp_next>0) {active=&comp_next;}
      else
        if(stackzero_next!=NULL && 
           stackzero_next-compzero_next>0) {active=&compzero_next;}
  
      if(active==NULL) ENDRUN("no active, while stack still >0\n");

      // iterate over all unvisited elements
      if(stack_next!=NULL)
      {
        //~ LOG("check massive %d\n", rest_next-stack_next+1);
        for (struct particle *i = stack_next; i <= rest_next; i++)
        {
          diag->tcount[clevel]++;
          // if element is connected to the first element of the stack
          if ( ((DOUBLE) timestep_ij(*active, i,dir)) <= dt)
          {
            // add i to the end of the stack by swapping stack_next and i
            //~ LOG("stack_next add %d\n", i->id);
            //~ LOG("stack offsets: %d, %d\n", stack_next-s.part, i-s.part);
            SWAP( *stack_next , *i, struct particle );
            stack_next++;
            stack_size++;
          }
        }
      }
      // iterate over all unvisited elements
      if(stackzero_next!=NULL)
      {
        //~ LOG("check zero %d\n", restzero_next-stackzero_next+1);
        for (struct particle *i = stackzero_next; i <= restzero_next; i++)
        {
          diag->tcount[clevel]++;
          // if element is connected to the first element of the stack
          if ( ((DOUBLE) timestep_ij(*active, i,dir)) <= dt)
          {
            // add i to the end of the stack by swapping stack_next and i
            //~ LOG("stackzero_next add %d\n", i->id);
            //~ LOG("stack offsets: %d, %d\n", stackzero_next-s.part, i-s.part);
            SWAP( *stackzero_next , *i, struct particle );
            stackzero_next++;
            stack_size++;
          }
        }
      }
      // pop the stack
      (*active)++;
      if(active==&compzero_next) compzero_size++;
      comp_size++;
      stack_size--;
      //~ LOG("popped %d, %d, %d\n", stack_size, comp_size, compzero_size);

    }
    processed += comp_size;
    //~ LOG("comp finish %d, %d\n", comp_size, compzero_size);
    // new component is non-trivial: create a new sys
    if (comp_size > 1)
    {
      //~ LOG("split_cc: found component with size: %d %d\n", comp_size, compzero_size);
      //~ LOG("%d %d \n", comp_next-stack_next, compzero_next-stackzero_next);
      c_next->n = comp_size;
      c_next->nzero = compzero_size;
      if(comp_size-compzero_size>0)
      {
        c_next->part = comp_next - (comp_size-compzero_size);
        c_next->last = comp_next-1;
      }
      if(compzero_size>0)
      {
        c_next->zeropart = compzero_next - compzero_size;
        c_next->lastzero = compzero_next-1;
      }
      if(c_next->part==NULL) c_next->part=c_next->zeropart;
      //~ PRINTSYS((*c_next));
      //~ PRINTOFFSETS((*c_next));

      c_next->next_cc = (struct sys*) malloc( sizeof(struct sys) );
      c_next = c_next->next_cc;
      *c_next=zerosys;
    }
    else  // new component is trivial: add to rest, reset pointers
    {
      //~ LOG("split_cc: add to rest\n");
      //~ LOG("%d %d \n", comp_next-stack_next, compzero_next-stackzero_next);
      
      if(active==&comp_next)
      {
        comp_next--;
        //~ LOG("r1 check offsets: %d, %d\n", comp_next-s.part, rest_next-s.part);
        
        SWAP( *comp_next, *rest_next, struct particle );
        rest_next--;
        stack_next--;
      } else
      {
        compzero_next--;
        //~ LOG("r2 check offsets: %d, %d\n", compzero_next-s.part, restzero_next-s.part);
        SWAP( *compzero_next, *restzero_next, struct particle );
        restzero_next--;
        stackzero_next--; 
      }
    }
  }
  if(stack_next!=NULL && stack_next!=rest_next+1) ENDRUN("unexpected")
  if(stackzero_next!=NULL && stackzero_next!=restzero_next+1) ENDRUN("unexpected")

  // create the rest system 
  *r=zerosys;
  if(rest_next!=NULL) r->n = s.last - rest_next;
  if(restzero_next!=NULL) r->nzero = s.lastzero - restzero_next;
  r->n+=r->nzero;
  if (r->n-r->nzero > 0)
  {
    r->part = rest_next+1;
    r->last = s.last;
  }
  if (r->nzero > 0)
  {
    r->zeropart = restzero_next+1;
    r->lastzero = s.lastzero;
  }
  if(r->part==NULL) r->part=r->zeropart;

  if (processed != s.n)
  {
    ENDRUN("split_cc particle count mismatch: processed=%u s.n=%u r->n=%u\n", processed, s.n, r->n);
  }

  //~ LOG("exit with %d %d\n", s.n, s.nzero);

}



void split_cc_verify(int clevel,struct sys s, struct sys *c, struct sys *r) {
  /*
   * split_cc_verify: explicit verification if connected components c and rest system r form a correct
   * connected components decomposition of the system.
   */
  LOG("split_cc_verify ping s.n=%d r->n=%d\n", s.n, r->n);
  //LOG_CC_SPLIT(c, r);
  UINT pcount_check = 0;

  for (UINT i = 0; i < s.n; i++)
  {
    pcount_check = 0;
    UINT particle_found = 0;
    struct particle *p = GETPART(s, i);
    for (struct sys *cj = c; !IS_ZEROSYS(cj); cj = cj->next_cc)
    {
      verify_split_zeromass(*cj);
      pcount_check += cj->n;
      //~ //LOG("%d\n", pcount_check);
      // search for p in connected components
      for (UINT k = 0; k < cj->n; k++)
      {
        struct particle * pk = GETPART( *cj,k);
        // is pk equal to p
        if (p->id == pk->id)
        {
          particle_found += 1;
          //~ LOG("split_cc_verify: found %d in a cc\n",i);
        }
      }
      if (cj->n-cj->nzero>0 &&  (  GETPART( *cj, cj->n - cj->nzero - 1) != cj->last ))
      {
        LOG("split_cc_verify: last pointer for c is not set correctly!\n");
        LOG_CC_SPLIT(c, r);
        ENDRUN("data structure corrupted\n");
      }
      if (cj->nzero>0 &&  (  GETPART( *cj, cj->n-1) != cj->lastzero ))
      {
        LOG("split_cc_verify: last pointer for c is not set correctly!\n");
        LOG_CC_SPLIT(c, r);
        ENDRUN("data structure corrupted\n");
      }
    }

    verify_split_zeromass(*r);

    // search for p in rest
    for (UINT k = 0; k < r->n; k++)
    {
      struct particle * pk = GETPART( *r, k);

      // is pk equal to p
      if (p->id == pk->id)
      {
        particle_found += 1;
        //~ LOG("found at r\n")
      }
    }

    if (particle_found != 1)
    {
      LOG("split_cc_verify: particle %d (%d) particle_found=%d\n", i, p->id, particle_found);
      LOG_CC_SPLIT(c, r);
      ENDRUN("data structure corrupted\n");
    }
  }

  //if (& ( r->part[r->n - 1] ) != r->last) {
  //  LOG("split_cc_verify: last pointer for r is not set correctly! %d %d",&( r->part[r->n - 1] ), r->last);
  //  LOG_CC_SPLIT(c, r);
  //  ENDRUN("data structure corrupted\n");
  //}

  if (pcount_check + r->n != s.n)
  {
    LOG("split_cc_verify: particle count mismatch (%d %d)\n", pcount_check + r->n, s.n);
    LOG_CC_SPLIT(c, r);
    ENDRUN("data structure corrupted\n");
    //ENDRUN("split_cc_verify: particle count mismatch\n");
  }
  else
  {
     LOG("split_cc_verify pong\n");
  }
  //ENDRUN("Fin.\n");
}

void split_cc_verify_ts(int clevel,struct sys *c, struct sys *r, DOUBLE dt)
{
  DOUBLE ts_ij;
  int dir=SIGN(dt);
  dt=fabs(dt);
  // verify C-C interactions
  for (struct sys *ci = c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
    for (UINT i = 0; i < ci->n; i++)
    {
      for (struct sys *cj = c; !IS_ZEROSYS(cj); cj = cj->next_cc)
      {
        if (ci == cj)
        {
          continue;
        }
        for (UINT j = 0; j < cj->n; j++)
        {
          ts_ij = (DOUBLE) timestep_ij(GETPART( *ci, i), GETPART( *cj, j), dir);
          //LOG("comparing %d %d\n", ci->part[i].id, cj->part[j].id);
          //LOG("%f %f \n", ts_ij, dt);
          if (dt > ts_ij)
          {
            ENDRUN("split_cc_verify_ts C-C timestep underflow\n");
          }
        }
      }
    }
  }

  // verify C-R interactions
  for (struct sys *ci = c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
    for (UINT i = 0; i < ci->n; i++)
    {
      for (UINT j = 0; j < r->n; j++)
      {
        ts_ij = (DOUBLE) timestep_ij( GETPART(*ci, i), GETPART(*r, j),dir);
        if (ts_ij < dt)
        {
          ENDRUN("split_cc_verify_ts C-R timestep underflow\n");
        }
      }
    }
  }

  // verify R interactions
  for (UINT i = 0; i < r->n; i++)
  {
    for (UINT j = 0; j < r->n; j++)
    {
      if (i == j) continue;
      ts_ij = (DOUBLE) timestep_ij( GETPART(*r, i), GETPART( *r,j),dir);
      if (ts_ij < dt)
      {
        ENDRUN("split_cc_verify_ts R-R timestep underflow\n");
      }
    }
  }
}

// TODO rename to cc_free_sys?
void free_sys(struct sys * s)
{
  if (s==NULL) return;
  if (s->next_cc != NULL)
  {
    free_sys(s->next_cc);
  }
  free(s);
}

DOUBLE sys_forces_max_timestep(struct sys s,int dir)
{
  DOUBLE ts = 0.0;
  DOUBLE ts_ij;
  for (UINT i = 0; i < s.n-1; i++)
  {
    for (UINT j = i+1; j < s.n; j++)
    {
      ts_ij = (DOUBLE) timestep_ij(GETPART(s,i), GETPART(s,j) ,dir); // check symm.
      if (ts_ij >= ts) { ts = ts_ij; };
    }
  }
  return ts;
}

#define BS_SUBSYS_SIZE   10
#define TASKCONDITION    (nc > 1 && s.n>BS_SUBSYS_SIZE)
void evolve_cc2(int clevel,struct sys s, DOUBLE stime, DOUBLE etime, DOUBLE dt, int inttype, int recenter)
{
  DOUBLE cmpos[3],cmvel[3];
  int recentersub=0;
  struct sys c = zerosys, r = zerosys;
  CHECK_TIMESTEP(etime,stime,dt,clevel);

  //~ if(accel_zero_mass) split_zeromass(&s);

  if ((s.n == 2 || s.n-s.nzero<=1 )&& (inttype==CCC_KEPLER || inttype==CC_KEPLER))
  //~ if (s.n == 2 && (inttype==CCC_KEPLER || inttype==CC_KEPLER))
  {
    evolve_kepler(clevel,s, stime, etime, dt);
    return;
  }

  if (s.n <= BS_SUBSYS_SIZE && (inttype==CCC_BS ||inttype==CC_BS))
  {
    evolve_bs(clevel,s, stime, etime, dt);
    return;
  }

  if (s.n <= BS_SUBSYS_SIZE && (inttype==CCC_BSA ||inttype==CC_BSA))
  {
    evolve_bs_adaptive(clevel,s, stime, etime, dt,1);
    return;
  }

  if(recenter && (inttype==CCC || inttype==CCC_KEPLER || inttype==CCC_BS || inttype==CCC_BSA))
  {
     system_center_of_mass(s,cmpos,cmvel);
     move_system(s,cmpos,cmvel,-1);
  }

// not actually helpful I think; needs testing
#ifdef CC2_SPLIT_SHORTCUTS
  int dir=SIGN(dt);
  DOUBLE initial_timestep = sys_forces_max_timestep(s, dir);
  if(fabs(dt) > initial_timestep)
  {
    DOUBLE dt_step = dt;
    while (fabs(dt_step) > initial_timestep)
    {
      dt_step = dt_step / 2;
      clevel++;
    }
    LOG("CC2_SPLIT_SHORTCUTS clevel=%d dt/dt_step=%Le\n", clevel,(long double) (dt / dt_step));
    for (DOUBLE dt_now = 0; dir*dt_now < dir*(dt-dt_step/2); dt_now += dt_step)
      evolve_cc2(clevel,s, dt_now, dt_now + dt_step, dt_step,inttype,0);
    return;
  }
#endif

#ifdef CONSISTENCY_CHECKS
  if (clevel == 0)
  {
    printf("consistency_checks: ", s.n, clevel);
  }
#endif

#ifdef CONSISTENCY_CHECKS
  // debug: make a copy of s to verify that the split has been done properly
  struct sys s_before_split=zerosys;
  s_before_split.n = s.n;
  s_before_split.nzero = s.nzero;
  s_before_split.part = (struct particle*) malloc(s.n*sizeof(struct particle));
  if(s_before_split.n-s_before_split.nzero>0) s_before_split.last = s_before_split.part+(s_before_split.n-s_before_split.nzero)-1;
  if(s_before_split.nzero>0) s_before_split.zeropart = s_before_split.last+1;
  if(s_before_split.nzero>0) s_before_split.lastzero = s_before_split.part+s_before_split.n-1;
  s_before_split.next_cc = NULL;
  for(UINT i=0; i<s.n;i++) *GETPART(s_before_split, i)=*GETPART(s,i);
#endif


  /*
   split_cc() decomposes particles in H (eq 25) into:
   1) K non-trivial connected components C_1..C_K
   2) Rest set R
  */
  split_cc(clevel,s, &c, &r, dt);
  //if (s.n != c.n) LOG_CC_SPLIT(&c, &r); // print out non-trivial splits

#ifdef CONSISTENCY_CHECKS
/*
    if (s.n != r.n) {
    LOG("s: ");
    LOGSYS_ID(s_before_split);
    LOG("c: ");
    LOGSYSC_ID(c);
    LOG("r: ");
    LOGSYS_ID(r);
  }
*/
  // verify the split
  split_cc_verify(clevel,s_before_split, &c, &r);
  split_cc_verify_ts(clevel,&c, &r, dt);
  free(s_before_split.part);
  if (clevel == 0) {
    printf("ok ");
  }
#endif

  if (IS_ZEROSYSs(c)) {
    diag->deepsteps++;
    diag->simtime+=dt;
  }

  // Independently integrate every C_i at reduced pivot time step h/2 (1st time)
  int nc=0; for (struct sys *ci = &c; !IS_ZEROSYS(ci); ci = ci->next_cc) nc++;
  
  if(nc>1 || r.n>0) recentersub=1;

  for (struct sys *ci = &c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
#ifdef _OPENMP
    if( TASKCONDITION )
    {
      diag->ntasks[clevel]++;
      diag->taskcount[clevel]+=ci->n;
#pragma omp task firstprivate(clevel,ci,stime,dt,recentersub) untied
      {
        struct sys lsys=zerosys;
        lsys.n=ci->n;
        lsys.nzero=ci->nzero;
        struct particle* lpart=(struct particle*) malloc(lsys.n*sizeof(struct particle));
        lsys.part=lpart;
        if(lsys.n-lsys.nzero>0) lsys.last=lpart+lsys.n-lsys.nzero-1;
        if(lsys.nzero>0) lsys.zeropart=lsys.last+1;
        if(lsys.nzero>0) lsys.lastzero=lpart+lsys.n-1;
        
        for(UINT i=0;i<lsys.n;i++) *GETPART(lsys,i)=*GETPART(*ci,i);
      
        evolve_cc2(clevel+1,lsys, stime, stime+dt/2, dt/2,inttype,recentersub);

        for(UINT i=0;i<lsys.n;i++) *GETPART(*ci,i)=*GETPART(lsys,i);
      
        free(lpart);
      }
    } else
#endif
  {
      evolve_cc2(clevel+1,*ci, stime, stime+dt/2, dt/2,inttype,recentersub);
  }
  }
#pragma omp taskwait

  // Apply drifts and kicks at current pivot time step (eq 30)
  if(r.n>0) drift(clevel,r, stime+dt/2, dt/2); // drift r, 1st time

  // kick ci <-> cj (eq 23)
  for (struct sys *ci = &c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
    for (struct sys *cj = &c; !IS_ZEROSYS(cj); cj = cj->next_cc)
    {
      if (ci != cj)
      {
        kick(clevel,*ci, *cj, dt);
        //kick(*cj, *ci, dt);
      }
    }
  }

  //~ if(r.n>0 && accel_zero_mass) split_zeromass(&r);
  // kick c <-> rest (eq 24)
  if(r.n>0) for (struct sys *ci = &c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
    kick(clevel,r, *ci, dt);
    kick(clevel,*ci, r, dt);
  }

  if(r.n>0) kick(clevel,r, r, dt); // kick rest (V_RR)

  if(r.n>0) drift(clevel,r, etime, dt/2); // drift r, 2nd time

  // Independently integrate every C_i at reduced pivot time step h/2 (2nd time, eq 27)
  for (struct sys *ci = &c; !IS_ZEROSYS(ci); ci = ci->next_cc)
  {
#ifdef _OPENMP
    if (TASKCONDITION)
    {
      diag->ntasks[clevel]++;
      diag->taskcount[clevel]+=ci->n;
#pragma omp task firstprivate(clevel,ci,stime,etime,dt,recentersub) untied
      {
        struct sys lsys=zerosys;
        lsys.n=ci->n;
        lsys.nzero=ci->nzero;
        struct particle* lpart=(struct particle*) malloc(lsys.n*sizeof(struct particle));
        lsys.part=lpart;
        if(lsys.n-lsys.nzero>0) lsys.last=lpart+lsys.n-lsys.nzero-1;
        if(lsys.nzero>0) lsys.zeropart=lsys.last+1;
        if(lsys.nzero>0) lsys.lastzero=lpart+lsys.n-1;
        
        for(UINT i=0;i<lsys.n;i++) *GETPART(lsys,i)=*GETPART(*ci,i);
        
        evolve_cc2(clevel+1,lsys, stime+dt/2, etime, dt/2,inttype,recentersub);
        
        for(UINT i=0;i<lsys.n;i++) *GETPART(*ci,i)=*GETPART(lsys,i);
        
        free(lpart);
      }
    } else
#endif
    {
      evolve_cc2(clevel+1,*ci, stime+dt/2, etime, dt/2,inttype,recentersub);
    }
  }
#pragma omp taskwait

  if(recenter && (inttype==CCC || inttype==CCC_KEPLER || inttype==CCC_BS || inttype==CCC_BSA))
  {
    for(int i=0;i<3;i++) cmpos[i]+=cmvel[i]*dt;
    move_system(s,cmpos,cmvel,1);
  }

  free_sys(c.next_cc);

  //~ if(accel_zero_mass) split_zeromass(&s);
}
#undef TASKCONDITION
