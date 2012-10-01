import ast
import math
import collections
from radon.visitors import HalsteadVisitor
from radon.complexity import cc_visit_ast, average_complexity
from radon.raw import analyze


# Halstead metrics
Halstead = collections.namedtuple('Halstead', 'h1 h2 N1 N2 vocabulary length '
                                              'calculated_length volume '
                                              'difficulty effort time bugs')


def compute_mi(halstead_volume, complexity, sloc, comments):
    '''Compute the Maintainability Index (MI) given the Halstead Volume, the
    Cyclomatic Complexity, the SLOC number and the number of comment lines.
    Usually it is not used directly but instead
    :func:`~radon.metrics.mi_visit` is preferred.
    '''
    sloc_scale = math.log(sloc) if sloc > 0 else 0
    volume_scale = math.log(halstead_volume) if halstead_volume > 0 else 0
    comments_scale = math.sqrt(2.46 * comments) if comments != 0 else 0
    return max(0, (171 - 5.2 * volume_scale - .23 * complexity -
                   16.2 * sloc_scale + 50 * math.sin(comments)) * 100 / 171.)


def h_visit(code):
    '''Compile the code into an AST tree and then pass it to
    :func:`~radon.metrics.h_visit_ast`.
    '''
    return h_visit_ast(ast.parse(code))


def h_visit_ast(ast_node):
    '''Visit the AST node using the :class:`~radon.visitors.HalsteadVisitor`
    visitor. A namedtuple with the following fields is returned:

        * h1: the number of distinct operators
        * h2: the number of distinct operands
        * N1: the total number of operators
        * N2: the total number of operands
        * h: the vocabulary, i.e. h1 + h2
        * N: the length, i.e. N1 + N2
        * calculated_length: h1 * log2(h1) + h2 * log2(h2)
        * volume: V = N * log2(h)
        * difficulty: D = h1 / 2 * N2 / h2
        * effort: E = D * V
        * time: T = E / 18 seconds
        * bugs: B = V / 3000 - an estimate of the errors in the implementation
    '''
    visitor = HalsteadVisitor.from_ast(ast_node)
    h1, h2 = visitor.distinct_operators, visitor.distinct_operands
    N1, N2 = visitor.operators, visitor.operands
    h = h1 + h2
    N = N1 + N2
    volume = math.log(h ** N, 2)
    difficulty = (h1 * N2) / float(2 * h2) if h2 != 0 else 0
    effort = difficulty * volume
    return Halstead(
        h1, h2, N1, N2, h, N, h1 * math.log(h1, 2) + h2 * math.log(h2, 2),
        volume, difficulty, effort, effort / 18., volume / 3000.
    )


def mi_parameters(code, count_multi=True):
    '''Given a source code snippet, compute the necessary parameters to
    compute the Maintainability Index metric. These include:

        * the Halstead Volume
        * the Cyclomatic Complexity
        * the number of LLOC (Logical Lines of Code)
        * the percent of lines of comment
    
    :param multi: If True, then count multiline strings as comment lines as
        well. This is not always safe because Python multiline strings are not
        always docstrings.
    '''
    ast_node = ast.parse(code)
    raw = analyze(code)
    comments_lines = raw.comments + (raw.multi if count_multi else 0)
    comments = raw.comments / float(raw.sloc) * 100
    return (h_visit_ast(ast_node).volume,
            average_complexity(cc_visit_ast(ast_node)), raw.lloc, comments)


def mi_visit(code, multi):
    '''Visit the code and compute the Maintainability Index (MI) from it.
    '''
    return compute_mi(*mi_parameters(code, multi))
