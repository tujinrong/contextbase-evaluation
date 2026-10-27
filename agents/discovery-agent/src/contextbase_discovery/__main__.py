from contextbase_runtime.cli import main as agent_main
from .agent import DiscoveryAgent


def main(argv=None):
    return agent_main(DiscoveryAgent, argv)


if __name__ == '__main__':
    raise SystemExit(main())
