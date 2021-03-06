import numpy
import cplex

from cplex.exceptions import CplexError

from Base import BiobjectiveSolver


class DoubleEpsilonConstraintSolver(BiobjectiveSolver):
    """
        Solves a modification of the epsilon constraint problem.
        Epsilon bound is applied from top and bottom vertices in
        an alternating fashion, such that the previous solved
        problem can be used as warm start to the current one
    """

    def solve(self):
        """
            solves the double epsilon constraint problem and returns the exact pareto front
        """
        pq = []
        try:
            #init problem/rectangle
            z_t, r_t = self._lexmin(0, 1, cplex.infinity)
            z_b, r_b = self._lexmin(1, 0, cplex.infinity)
            self._solutions.append(z_t)
            self._solutions.append(z_b)
            pq.append((z_t.objs, z_b.objs, r_b))

            while pq:
                z1_objs, z2_objs, warmstart = pq.pop()
                print "\n\nCurrent bounds" , z1_objs, z2_objs,"\n\n"
                z1_hat, r1_hat = self._lexmin(0, 1, z1_objs[1] - BiobjectiveSolver.EPS, warmstart=warmstart)

                if numpy.allclose(z1_hat.objs, z2_objs):
                    break

                z2_hat, r2_hat = self._lexmin(1, 0, z2_objs[0] - BiobjectiveSolver.EPS, warmstart=r1_hat)

                if numpy.allclose(z2_hat.objs, z1_objs) or numpy.allclose(z2_hat.objs, z1_hat.objs):
                    break

                self._solutions.append(z1_hat)
                self._solutions.append(z2_hat)
                pq.append((z1_hat.objs, z2_hat.objs, r2_hat))

        except CplexError, exc:
            print exc
            return

        return self._solutions

    def approximate(self, eps):
        """
            approximates the pareto front with an epsilon bound on precission.
            it uses the notion of hypervolume indicator (resp. modified hypervolume indicator)

            it calculates the area of the intersecting polygon of the currently found pareto points,
            (zt,zb)- R^2_>= [ H(y)], and the spanning search rectangles [h(y)]. The differ h(y) - H(y)
            is the quantitative measure of the approximation of the pareto front

            for calculating the areas a clipping algorithm has been used (don't know jet which one)

            @param eps: the precision of approximation [0.0,1.0] where 0.0 indicates an exact calculation
            @return: A list of pareto points as Solution objects
        """
        if eps <= 0.0:
            return self.solve()

        pq = []
        search_rectangles = set()
        try:
            #init problem/rectangle
            z_t, r_t = self._lexmin(0, 1, cplex.infinity)
            z_b, r_b = self._lexmin(1, 0, cplex.infinity)
            self._solutions.append(z_t)
            init_rectangle = (z_t.objs, z_b.objs)
            self._solutions.append(z_b)

            pq.append((z_t.objs, z_b.objs, r_b))

            while pq:
                z1_objs, z2_objs, warmstart = pq.pop()
                #print z1_objs, z2_objs,
                z1_hat, r1_hat = self._lexmin(0, 1, z1_objs[1] - BiobjectiveSolver.EPS, warmstart=warmstart)
                self._solutions.append(z1_hat)
                search_rectangles.add((z1_objs, z1_hat.objs))

                gap = self._hypervol.calc_hypervol_gap(self._solutions, init_rectangle, search_rectangles)
                #print "Hypergap ", gap
                if gap <= eps:
                    return self._solutions

                if numpy.allclose(z1_hat.objs, z2_objs):
                    return self._solutions

                z2_hat, r2_hat = self._lexmin(1, 0, z2_objs[0] - BiobjectiveSolver.EPS, warmstart=r1_hat)
                self._solutions.append(z2_hat)
                search_rectangles.add((z2_hat.objs, z2_objs))

                gap = self._hypervol.calc_hypervol_gap(self._solutions, init_rectangle, search_rectangles)
                #print "Hypergap ", gap
                if gap <= eps:
                    return self._solutions

                if numpy.allclose(z2_hat.objs, z1_objs) or z2_hat == z1_hat:
                    return self._solutions

                pq.append((z1_hat.objs, z2_hat.objs, r2_hat))

        except CplexError, exc:
            print exc
            return

        return self._solutions
