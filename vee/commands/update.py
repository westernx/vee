from vee.cli import style, style_note
from vee.commands.main import command, argument, group
from vee.environment import Environment


@command(
    argument('--all', action='store_true', help='update all repos'),
    argument('--force', action='store_true', help='force checkout, even if not fast-forward'),
    argument('repos', nargs='*'),
    help='update repos',
)
def update(args):

    home = args.assert_home()

    if args.all:
        env_repos = list(home.iter_repos())
    else:
        env_repos = [home.get_env_repo(x) for x in args.repos] if args.repos else [home.get_env_repo()]

    retcode = 0

    for env_repo in env_repos:

        print style_note('Updating repo', env_repo.name)

        env_repo.clone_if_not_exists()
        rev = env_repo.fetch()

        if not args.force and not env_repo.check_ff_safety(rev):
            print style('Error:', 'red', bold=True), style('Cannot fast-forward; skipping.', bold=True)
            retcode = retcode or 1
            continue

        print 'CHECKING OUT', rev
        env_repo.checkout(force=args.force)

    return retcode
