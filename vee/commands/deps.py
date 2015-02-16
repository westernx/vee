from vee.commands.main import command, argument
from vee.requirement import Requirement
from vee.utils import colour


@command(
    argument('-p', '--provisions', action='store_true'),
    argument('package', nargs='...'),
    help='list dependencies of a package',
    usage='vee deps PACKAGE [OPTIONS]',
)
def deps(args):
    args.assert_home()
    req = Requirement(args.package, home=args.home)

    to_check = [req]
    seen = set([str(req)])

    while to_check:

        req = to_check.pop(0)

        for dep in req.manager.dependencies():
            if str(dep) in seen:
                continue
            to_check.append(dep)
            seen.add(str(dep))
            if not args.provisions:
                print dep

        if args.provisions:
            for pro in req.manager.provisions():
                print pro

    
