from vee.commands.main import command, argument
from vee.environment import Environment
from vee.requirement import Requirement
from vee.requirementset import RequirementSet
from vee.utils import style
from vee.exceptions import CliException, AlreadyInstalled


@command(
    argument('--force-install', action='store_true'),
    argument('--raw', action='store_true', help='package is directory, not a requirement'),
    argument('--long-names', action='store_true',
        help='automatically picks package names'),
    argument('environment'),
    argument('specification', nargs='...'),
    help='link a package',
    usage='vee link [--raw] ENVIRONMENT SPECIFICATION',
)
def link(args):

    args.assert_home()

    env = Environment(args.environment, home=args.home)

    if args.raw:
        for dir_ in args.package:
            print style('Linking', 'blue', bold=True), style(dir_, bold=True)
            env.link_directory(dir_)
        return


    req_set = RequirementSet()
    req_set.parse(args.specification[0], home=args.home)

    if not args.long_names:
        req_set.guess_names()

    for req in req_set.iter_requirements():

        if not args.force_install:
            req.package.resolve_existing(env=env) or req.package.resolve_existing()

        try:
            req.install(force=args.force_install)
        except AlreadyInstalled:
            pass
        
        frozen = req.package.freeze()
        
        print style('Linking', 'blue', bold=True), style(str(frozen), bold=True)

        req.package.link(env)
        


