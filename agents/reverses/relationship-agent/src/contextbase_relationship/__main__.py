from contextbase_runtime.cli import main as agent_main
from .agent import RelationshipAgent


def main(argv=None):
    return agent_main(RelationshipAgent, argv)


if __name__ == '__main__':
    raise SystemExit(main())
