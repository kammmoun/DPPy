# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt
import scipy.linalg as la

import functools  # used for decorators to pass docstring
# For DescentProcess class
import re  # to convert class names to string in

# For class UST
import networkx as nx
from itertools import chain  # to create edges of graph generated by __wilson
from dppy.exact_sampling import proj_dpp_sampler_eig_GS

# For class PoissonizedPlancherel
from bisect import bisect_right  # for _RSK
from matplotlib import collections as mc  # see plot_diagram


##########################
# Uniform Spanning trees #
##########################
class UST:
    """ Uniform Spanning Tree object parametrized by

    :param graph:
        Connected undirected graph

    :type graph:
        networkx graph

    .. seealso::

        - :ref:`finite_dpps_definition`
        - :ref:`UST`
    """

    def __init__(self, graph):

        self.graph = graph

        self.nodes = list(self.graph.nodes())
        self.nb_nodes = len(self.graph)

        self.edges = list(self.graph.edges())
        self.nb_edges = self.graph.number_of_edges()

        self.neighbors = [list(graph.neighbors(v))
                          for v in range(self.nb_nodes)]

        self.sampling_mode = 'Wilson'
        self.list_of_samples = []

        self.kernel = None
        self.kernel_eig_vecs = None

        # self.list_ST_edge_labels = None
        # degrees = [g.degree(v) for v in nodesices]
        # transition_proba = [[1./deg]*deg for deg in degrees]

    def __str__(self):

        str_info = ['Uniform Spanning Tree measure on a graph with:',
                    '- {} nodes'.format(self.nb_nodes),
                    '- {} edges'.format(self.nb_edges),
                    'Sampling mode = {}'.format(self.sampling_mode),
                    'Number of samples = {}'.format(len(self.list_of_samples))]

        return '\n'.join(str_info)

    def info(self):
        """ Print infos about the :class:`UST` object
        """
        print(self.__str__())

    def flush_samples(self):
        """ Empty the ``UST.list_of_samples`` attribute.
        """
        self.list_of_samples = []

    def sample(self, mode='Wilson'):
        """ Sample exactly from Unif :class:`UST <UST>` object by computing the eigenvalues of random matrices.
        Generates a networkx graph object.

        :param mode:

            - ``'Wilson'``
            - ``'Aldous-Broder'``
            - ``'DPP_exact'``

        :type mode:
            string, default ``'Wilson'``

        .. seealso::

            - Wilson algorithm :cite:`PrWi98`
            - Aldous-Broder :cite:`Ald90`
        """

        self.sampling_mode = mode

        if self.sampling_mode == 'Wilson':
            sampl = self.__wilson()

        elif self.sampling_mode == 'Aldous-Broder':
            sampl = self.__aldous()

        elif self.sampling_mode == 'DPP_exact':

            if self.kernel_eig_vecs is None:
                self.__compute_kernel_eig_vecs()

            dpp_sample = proj_dpp_sampler_eig_GS(self.kernel_eig_vecs)

            g_finite_dpp = nx.Graph()
            edges_finite_dpp = [self.edges[e] for e in dpp_sample]
            g_finite_dpp.add_edges_from(edges_finite_dpp)

            sampl = g_finite_dpp

        else:
            raise ValueError('In valid `mode` argument. Choose among:\
                             `Wilson`, `Aldous-Broder`, `DPP_exact`.\n\
                             Given {}'.format(mode))

        self.list_of_samples.append(sampl)

    def compute_kernel(self):
        """ Compute the orthogonal projection kernel :math:`\mathbf{K}` onto the row span of the vertex-edge incidence matrix, refering to the transfer current matrix.
        In fact, one can discard any row of the vertex-edge incidence matrix (:math:`A`) to compute :math:`\mathbf{K}=A^{\top}[AA^{\top}]^{-1}A`.
        In practice, we orthogonalize the rows of :math:`A` to get the eigenvectors :math:`U` of :math:`\mathbf{K}` and thus compute :math:`\mathbf{K}=UU^{\top}`.

        .. seealso::

            - :func:`plot_kernel <plot_kernel>`
        """
        if self.kernel is None:
            if self.kernel_eig_vecs is None:
                self.__compute_kernel_eig_vecs()
            # K = UU.T
            self.kernel = self.kernel_eig_vecs.dot(self.kernel_eig_vecs.T)
        else:
            pass

    def __compute_kernel_eig_vecs(self):
        """Orthogonalize the rows of vertex-edge incidence matrix (:math:`A`) to get the eigenvectors :math:`U` of the kernel :math:`\mathbf{K}`.
        """

        vert_edg_inc = nx.incidence_matrix(self.graph, oriented=True)
        A = vert_edg_inc[:-1, :].toarray()  # Discard any row e.g. the last one
        # Orthonormalize rows of A
        self.kernel_eig_vecs, _ = la.qr(A.T, mode='economic')

    def plot(self, title=''):
        """ Display the last realization (spanning tree) of the corresponding :class:`UST` object.

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`sample <sample>`
        """

        graph_to_plot = self.list_of_samples[-1]

        plt.figure(figsize=(4, 4))

        pos = nx.circular_layout(graph_to_plot)
        nx.draw_networkx(graph_to_plot,
                         pos=pos,
                         node_color='orange',
                         with_labels=True)
        plt.axis('off')

        str_title = 'UST with {} algorithm'.format(self.sampling_mode)
        plt.title(title if title else str_title)

        # plt.savefig('sample_{}_{}.eps'.format(self.sampling_mode,len(self.list_of_samples)))

    def plot_graph(self, title=''):
        """Display the original graph defining the :class:`UST` object

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`compute_kernel <compute_kernel>`
        """

        edge_lab = [r'$e_{}$'.format(i) for i in range(self.nb_edges)]
        edge_labels = dict(zip(self.edges, edge_lab))
        node_labels = dict(zip(self.nodes, self.nodes))

        plt.figure(figsize=(4, 4))

        pos = nx.circular_layout(self.graph)
        nx.draw_networkx(self.graph,
                         pos=pos,
                         node_color='orange',
                         with_labels=True,
                         width=3)
        nx.draw_networkx_labels(self.graph,
                                pos,
                                node_labels)
        nx.draw_networkx_edge_labels(self.graph,
                                     pos,
                                     edge_labels,
                                     font_size=20)

        plt.axis('off')

        str_title = 'Original graph'
        plt.title(title if title else str_title)
        # plt.savefig('original_graph.eps')

    def plot_kernel(self, title=''):
        """Display a heatmap of the underlying orthogonal projection kernel :math:`\mathbf{K}` associated to the DPP underlying the :class:`UST` object

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`compute_kernel <compute_kernel>`
        """

        self.compute_kernel()

        fig, ax = plt.subplots(1, 1)

        heatmap = ax.pcolor(self.kernel, cmap='jet')

        ax.set_aspect('equal')

        ticks = np.arange(self.nb_edges)
        ticks_label = [r'${}$'.format(tic) for tic in ticks]

        ax.xaxis.tick_top()
        ax.set_xticks(ticks + 0.5, minor=False)

        ax.invert_yaxis()
        ax.set_yticks(ticks + 0.5, minor=False)

        ax.set_xticklabels(ticks_label, minor=False)
        ax.set_yticklabels(ticks_label, minor=False)

        str_title = 'UST kernel i.e. transfer current matrix'
        plt.title(title if title else str_title, y=1.08)

        plt.colorbar(heatmap)
        # plt.savefig('kernel.png')

    def __wilson(self, root=None):

        # Initialize the root, if root not specified start from any node
        n0 = root if root else np.random.choice(self.nb_nodes, size=1)[0]
        # -1 = not visited / 0 = in path / 1 = in tree
        nodes_state = -np.ones(self.nb_nodes, dtype=int)

        # Initialize the tree
        nodes_state[n0] = 1  # mark root it as in tree
        branches, tree_len = [], 1  # 1 for the root
        path = []  # temporary path

        while tree_len < self.nb_nodes:

            # visit a neighbor of n0 uniformly at random
            n1 = np.random.choice(self.neighbors[n0], size=1)[0]

            if nodes_state[n1] == -1:  # not visited => continue the walk

                path.extend([n1])  # add it to the path
                nodes_state[n1] = 0  # mark it as in the path
                n0 = n1  # continue the walk

            if nodes_state[n1] == 0:  # loop on the path => erase the loop

                knot = path.index(n1)  # find 1st appearence of n1 in the path
                nodes_loop = path[knot + 1:]  # identify nodes forming the loop
                del path[knot + 1:]  # erase the loop
                nodes_state[nodes_loop] = -1  # mark loopy nodes as not visited
                n0 = n1  # continue the walk

            elif nodes_state[n1] == 1:  # hits the tree => new branch

                if tree_len == 1:
                    branches.append([n1] + path)  # initial branch of the tree
                else:
                    branches.append(path + [n1])  # path as a new branch

                nodes_state[path] = 1  # mark the nodes as in the tree
                tree_len += len(path)  # update the length of the tree

                # Restart the walk from a random node among those not visited
                nodes_not_visited = np.where(nodes_state == -1)[0]
                if nodes_not_visited.size > 0:
                    n0 = np.random.choice(nodes_not_visited, size=1)[0]
                    path = [n0]

        wilson_tree_graph = nx.Graph()
        tree_edges = list(chain.from_iterable(
                            map(lambda x: zip(x[:-1], x[1:]), branches)))
        wilson_tree_graph.add_edges_from(tree_edges)

        return wilson_tree_graph

    def __aldous(self, root=None):

        # Initialize the root, if root not specified start from any node
        n0 = root if root else np.random.choice(self.nb_nodes, size=1)[0]

        # Initialize the tree
        tree_edges, tree_len = [], 1
        visited = np.zeros(self.nb_nodes, dtype=bool)
        visited[n0] = True

        while tree_len < self.nb_nodes:

            # visit a neighbor of n0 uniformly at random
            n1 = np.random.choice(self.neighbors[n0], size=1)[0]

            if visited[n1]:  # visited => continue the walk
                pass

            else:  # not visited => save the edge (n0, n1) and continue walk
                tree_edges.append((n0, n1))
                visited[n1] = True  # mark it as in the tree
                tree_len += 1

            n0 = n1

        aldous_tree_graph = nx.Graph()
        aldous_tree_graph.add_edges_from(tree_edges)

        return aldous_tree_graph


###########
# Descent #
###########
class Descent:

    def __init__(self):

        self.name =\
            ' '.join(re.findall('[A-Z][^A-Z]*', self.__class__.__name__))
        self.list_of_samples = []
        self.size = 100

    @property
    def _bernoulli_param(self):
        return 0.5

    def flush_samples(self):
        """ Empty the ``list_of_samples`` attribute.
        """
        self.list_of_samples = []

    def _unif_permutation(self, N):

        tmp = np.arange(N)
        for i in range(N - 1, 1, -1):
            j = np.random.randint(0, i + 1)
            tmp[j], tmp[i] = tmp[i], tmp[j]

        return tmp

    def sample(self, size=100):
        pass

    def overplot_descent(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            ax, size = func(*args, **kwargs)

            # Spine options
            ax.spines['bottom'].set_position('center')
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Ticks options
            minor_ticks = np.arange(0, size + 1)
            major_ticks = np.arange(0, size + 1, 10)
            ax.set_xticks(major_ticks)
            ax.set_xticks(minor_ticks, minor=True)
            ax.set_xticklabels(major_ticks, fontsize=15)
            ax.xaxis.set_ticks_position('bottom')

            ax.tick_params(
                axis='y',           # changes apply to the y-axis
                which='both',       # both major and minor ticks are affected
                left=False,         # ticks along the left edge are off
                right=False,        # ticks along the right edge are off
                labelleft=False)    # labels along the left edge are off

            ax.xaxis.grid(True)
            ax.set_xlim([-1, size + 1])
            ax.legend(bbox_to_anchor=(0, 0.85),
                      frameon=False,
                      prop={'size': 15})

            # plt.show()

        return wrapper

    @overplot_descent
    def plot(self, title=''):
        """Display the process on the real line

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`sample <sample>`
            - :func:`plot_vs_bernoullis <plot_vs_bernoullis>`
        """

        self.name = self.__class__.__name__

        fig, ax = plt.subplots(figsize=(19, 2))

        sampl = self.list_of_samples[-1]
        ax.scatter(sampl, np.zeros_like(sampl),
                   color='blue',
                   s=20,
                   label=self.name)

        str_title = 'Realization of the {}'.format(self.name)
        plt.title(title if title else str_title)

        return ax, self.size

    @overplot_descent
    def plot_vs_bernoullis(self, title=''):
        """Display the process on the real line and compare it to a sequence of i.i.d. Bernoullis

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`sample <sample>`
            - :func:`plot <plot>`
        """

        fig, ax = plt.subplots(figsize=(19, 2))

        sampl = self.list_of_samples[-1]
        bern = np.where(np.random.rand(self.size) < self._bernoulli_param)[0]

        ax.scatter(sampl, np.ones_like(sampl),
                   color='b', s=20, label=self.name)
        ax.scatter(bern, -np.ones_like(bern),
                   color='r', s=20, label='Bernoullis')

        str_title = r'Realization of the {} process vs independent Bernoulli variables with parameter p={:.3f}'.format(self.name,
                                                  self._bernoulli_param)
        plt.title(title if title else str_title)

        return ax, self.size


class CarriesProcess(Descent):
    """ Carries process formed by the cumulative sum of i.i.d. digits in :math:`\{0, \dots, b-1\}`. This is a DPP on the natural integers with a non symmetric kernel.

    :param base:
        Base/radix

    :type base:
        int, default 10

    .. seealso::

        - :cite:`BoDiFu10`
        - :ref:`carries_process`
    """

    def __init__(self, base=10):
        super().__init__()
        self.base = base

    def __str__(self):

        str_info = ['Carries process in base {}'.format(self.base),
                    'Number of samples = {}'.format(len(self.list_of_samples))]

        return '\n'.join(str_info)

    @property
    def _bernoulli_param(self):
        return 0.5 * (1 - 1 / self.base)

    def sample(self, size=100):
        """ Compute the cumulative sum (in base :math:`b`) of a sequence of i.i.d. digits and record the position of carries.

        :param size:
            size of the sequence of i.i.d. digits in :math:`\{0, \dots, b-1\}`

        :type size:
            int
        """

        self.size = size
        A = np.random.randint(0, self.base - 1, self.size)
        B = np.mod(np.cumsum(A), self.base)

        X = np.zeros(size, dtype=bool)
        X[1:] = B[1:] < B[:-1]  # Record the descents i.e. carries

        carries = np.arange(0, self.size)[X]

        self.list_of_samples.append(carries)


class DescentProcess(Descent):
    """ This is a DPP on :math:'\{1,2,\dots,n-1}' with a non symmetric kernel appearing in (or as a limit) of the descent process on the symmetric group.

        .. seealso::

            - :cite:`BoDiFu10`
            - :ref:`carries_process`
    """

    def __init__(self):
        super().__init__()

    def __str__(self):

        str_info = ['Descent process',
                    'Number of samples = {}'.format(len(self.list_of_samples))]

        return '\n'.join(str_info)

    def sample(self, size=100):
        """ Draw a permutation uniformly at random and record the descents i.e. indices where :math:`\sigma(i+1) < \sigma(i)`.

        :param size:
            size of the sequence of i.i.d. digits in :math:`\{0, \dots, b-1\}`

        :type size:
            int
        """

        self.size = size

        sigma = self._unif_permutation(self.size + 1)

        X = np.zeros(self.size, dtype=bool)
        X = sigma[1:] < sigma[:-1]  # Record the descents
        descent = np.arange(0, self.size)[X]

        self.list_of_samples.append(descent)


class VirtualDescentProcess(Descent):
    """ This is a DPP on :math:'\{1,2,\dots,n-1}' with a non symmetric kernel appearing in (or as a limite) of the descent process on the symmetric group.

    .. seealso::

        - :cite:`Kam18`
    """

    def __init__(self, x_0=0.5):

        super().__init__()
        if not (0 <= x_0 <= 1):
            raise ValueError("x_0 must be in [0,1]")
        self.x_0 = x_0

    def __str__(self):

        str_info = ['Limitting Descent process for vitural permutations',
                    'Number of samples = {}'.format(len(self.list_of_samples))]

        return '\n'.join(str_info)

    @property
    def _bernoulli_param(self):
        return 0.5 * (1 - self.x_0**2)

    def sample(self, size=100):
        """ Draw a permutation uniformly at random and record the descents i.e. indices where :math:`\sigma(i+1) < \sigma(i)` and something else...

        :param size:
            size of the sequence of i.i.d. digits in :math:`\{0, \dots, b-1\}`

        :type size:
            int

        .. seealso::

            - :cite:`Kam18`, Sec ??

        .. todo::

            ask @kammmoun to complete the docsting and Section in see also
        """

        self.size = size

        sigma = self._unif_permutation(self.size + 1)

        X = np.zeros(self.size, dtype=bool)
        X = sigma[1:] < sigma[:-1]  # Record the descents

        Y = np.random.binomial(2, self.x_0, self.size + 1)\
            != np.ones(self.size + 1)
        Z = [i for i in range(self.size) if (((not Y[i]) and Y[i+1]) or ((not Y[i]) and (not Y[i+1]) and X[i]))] 

        descent = np.arange(0, self.size)[Z]

        self.list_of_samples.append(descent)


################
# Permutations #
################
class PoissonizedPlancherel:
    """ Poissonized Plancherel measure

    :param theta:
        Base/radix

    :type theta:
        int, default 10

    .. seealso::

        - :cite:`Bor09` Section 6
        - :ref:`poissonized_plancherel_measure`
    """

    def __init__(self, theta=10):

        self.theta = theta  # Poisson param = expected length of permutation
        self.list_of_young_diag = []
        self.list_of_samples = []

    def __str__(self):

        str_info = ['Poissonized Plancherel measure\
                    with parameter {}'.format(self.theta),
                    'Number of samples = {}'.format(len(self.list_of_samples))]

        return '\n'.join(str_info)

    def info(self):
        """ Print infos about the :class:`UST` object
        """
        print(self.__str__())

    def sample(self):
        """ Sample from the Poissonized Plancherel measure and build the associated process.
        """

        N = np.random.poisson(self.theta)
        sigma = self._unif_permutation(N)
        P, _ = self._RSK(sigma)

        # young_diag = [len(row) for row in P]
        young_diag = np.fromiter(map(len, P), dtype=int)
        self.list_of_young_diag.append(young_diag)
        # sampl = [len(row) - i + 0.5 for i, row in enumerate(P, start=1)]
        sampl = young_diag - np.arange(0.5, young_diag.size)
        self.list_of_samples.append(sampl)

    def _unif_permutation(self, N):

        tmp = np.arange(N)
        for i in range(N - 1, 1, -1):
            j = np.random.randint(0, i + 1)
            tmp[j], tmp[i] = tmp[i], tmp[j]

        return tmp

    def _RSK(self, sigma):
        """Apply Robinson-Schensted-Knuth correspondence on a sequence of reals, e.g. a permutation, and return the corresponding insertion and recording tableaux.

        :param sigma:
            Sequence of real numbers
        :type sigma:
            array_like

        :return:
            :math:`P, Q` insertion and recording tableaux
        :rtype:
            list
        """

        P, Q = [], []  # Insertion/Recording tableau

        for it, x in enumerate(sigma, start=1):

            # Iterate along the rows of the tableau P to find a place for the bouncing x and record the position where it is inserted
            for row_P, row_Q in zip(P, Q):

                # If x finds a place at the end of a row of P add it and record its position in the corresponding the row of Q
                if x >= row_P[-1]:
                    row_P.extend([x])
                    row_Q.extend([it])
                    break
                else:
                    # place x in row of P to keep the row ordered
                    ind_insert = bisect_right(row_P, x)
                    # Swap x with
                    x, row_P[ind_insert] = row_P[ind_insert], x

            # If no room for x at the end of any row of P create a new row
            else:
                P.append([x])
                Q.append([it])

        return P, Q

    def __xy_young_ru(self, young_diag):
        """ Compute the xy coordinates of the boxes defining the young diagram, using the russian convention.

        :param young_diag:
            points
        :type  young_diag:
            array_like

        :return:
            :math:`\omega(x)`
        :rtype:
            array_like
        """

        def intertwine(arr_1, arr_2):
            inter = np.empty((arr_1.size + arr_2.size,), dtype=arr_1.dtype)
            inter[0::2], inter[1::2] = arr_1, arr_2
            return inter

        # horizontal lines
        x_hor = intertwine(np.zeros_like(young_diag), young_diag)
        y_hor = np.repeat(np.arange(1, young_diag.size + 1), repeats=2)

        # vertical lines
        uniq, ind = np.unique(young_diag[::-1], return_index=True)
        gaps = np.ediff1d(uniq, to_begin=young_diag[-1])

        x_vert = np.repeat(np.arange(1, 1 + gaps.sum()), repeats=2)
        y_vert = np.repeat(young_diag.size - ind, repeats=gaps)
        y_vert = intertwine(np.zeros_like(y_vert), y_vert)

        xy_young_fr = np.column_stack([np.hstack([x_hor, x_vert]),
                                       np.hstack([y_hor, y_vert])])

        rot_45_and_scale = np.array([[1.0, -1.0],
                                     [1.0, 1.0]])

        return xy_young_fr.dot(rot_45_and_scale.T)

    def __limit_shape(self, x):
        """ Evaluate :math:`\omega(x)` the limit-shape function :cite:`Ker96`

        .. math::

            \omega(x) =
            \begin{cases}
                |x|, &\text{if } |x|\geq 2\\
                \frac{2}{\pi} \left(x \arcsin\left(\frac{x}{2}\right)
                                    + \sqrt{4-x^2} \right)
                    &\text{otherwise }
            \end{cases}

        :param x:
            points
        :type x:
            array_like

        :return:
            :math:`\omega(x)`
        :rtype:
            array_like

        .. seealso::

            - :func:`plot_diagram <plot_diagram>`
            - :cite:`Ker96`
        """

        w_x = np.empty(x.size, dtype=x.dtype)

        abs_x_gt2 = np.abs(x) >= 2.0

        w_x[abs_x_gt2] = np.abs(x[abs_x_gt2])
        w_x[~abs_x_gt2] = x[~abs_x_gt2] * np.arcsin(0.5 * x[~abs_x_gt2])\
                          + np.sqrt(4.0 - x[~abs_x_gt2]**2)
        w_x[~abs_x_gt2] *= 2.0 / np.pi

        return w_x

    def plot(self, title=''):
        """Display the process on the real line

        :param title:
            Plot title

        :type title:
            string

        .. seealso::

            - :func:`sample <sample>`
        """

        sampl = self.list_of_samples[-1]

        # Display the reparametrized Plancherel sample
        fig, ax = plt.subplots(figsize=(19, 2))

        ax.scatter(sampl, np.zeros_like(sampl), color='blue', s=20)

        # Spine options
        ax.spines['bottom'].set_position('center')
        ax.spines['left'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Ticks options
        x_max = np.max(np.abs(sampl)) + 0.5
        minor_ticks = np.arange(-x_max, x_max + 1)
        major_ticks = np.arange(-100, 100 + 1, 10)
        ax.set_xticks(major_ticks)
        ax.set_xticks(minor_ticks, minor=True)
        ax.set_xticklabels(major_ticks, fontsize=15)
        ax.xaxis.set_ticks_position('bottom')

        ax.tick_params(
            axis='y',           # changes apply to the y-axis
            which='both',       # both major and minor ticks are affected
            left=False,         # ticks along the left edge are off
            right=False,        # ticks along the right edge are off
            labelleft=False)    # labels along the left edge are off

        ax.xaxis.grid(True)
        ax.set_xlim([-x_max - 2, x_max + 2])
        # ax.legend(bbox_to_anchor=(0,0.85), frameon=False, prop={'size':20})

        str_title = r'Realization of the DPP associated to the Poissonized Plancherel measure with parameter $\theta=${}'.format(self.theta)
        plt.title(title if title else str_title)
        plt.show()

    def plot_diagram(self, normalization=False):
        """ Display the Young diagram (russian convention), the associated sample and potentially rescale the two to visualize the limit-shape theorem :cite:`Ker96`.
        The sample corresponds to the projection onto the real line of the descending surface edges.

        :param normalization:
            If ``normalization=True``, the Young diagram and the corresponding sample are scaled by a factor :math:`\sqrt{\theta}` and the limiting 

        :type normalization:
            bool, default False

        .. seealso::

            - :func:`sample <sample>`
            - :func:`plot <plot>`
            - :cite:`Ker96`
        """

        y_diag = self.list_of_young_diag[-1]
        sampl = self.list_of_samples[-1].copy()

        x_max = 1.1 * max(y_diag.size, y_diag[0])
        xy_young = self.__xy_young_ru(y_diag)

        if normalization:
            sampl /= np.sqrt(self.theta)
            x_max /= np.sqrt(self.theta)
            xy_young /= np.sqrt(self.theta)

        fig, ax = plt.subplots(figsize=(12, 8))

        # Display corresponding sample
        ax.scatter(sampl, np.zeros_like(sampl),
                   s=3, label='sample')
        # Display absolute value wedge
        ax.plot([-x_max, 0.0, x_max], [x_max, 0.0, x_max],
                c='k', lw=1)
        # Display young diagram in russian notation
        lc = mc.LineCollection(xy_young.reshape((-1, 2, 2)),
                               color='k', linewidths=2)
        ax.add_collection(lc)
        # Display limit shape
        if normalization:
            x_lim_sh = np.linspace(-x_max, x_max, 100)
            ax.plot(x_lim_sh, self.__limit_shape(x_lim_sh),
                    c='r', label='limit shape')

        # xy_y_diag = np.column_stack([y_diag,
        # np.arange(0.5, y_diag.size)]).dot(rot_45_and_scale.T)
        # if normalization:
        #     xy_y_diag /= np.sqrt(theta)
        # plt.scatter(xy_y_diag[:,0], np.zeros_like(y_diag), color='r')
        # plt.stem(xy_y_diag[:,0], xy_y_diag[:,1], linefmt='C0--', basefmt=' ')

        plt.legend(loc='best')
        plt.axis('equal')

        str_title = r'Young diagram associated to Poissonized Plancherel measure with parameter $\theta=${}'.format(self.theta)
        plt.title(str_title)
