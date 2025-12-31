#ifndef __GHOST_H__
#define __GHOST_H__
#include <stdio.h>
#include <stdlib.h>
#include "structures.h"

void build_ghost_list(int N, int size, int rank, LocalX *l_x);
void ghost_exchange(int N, int size, int rank, LocalX *l_x);

#endif 