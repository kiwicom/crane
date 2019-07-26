from crane.cli import cli


def test_no_subcommand(cli_runner):
    result = cli_runner.invoke(cli)
    assert result.exit_code == 0
    assert "Commands:\n" in result.output


def test_announce_no_event(cli_runner):
    result = cli_runner.invoke(cli, ["announce"])
    assert result.exit_code == 2
    assert "Missing argument" in result.output


def test_deploy_no_target(cli_runner):
    result = cli_runner.invoke(cli, ["deploy"])
    assert result.exit_code == 2
    assert "Missing argument" in result.output
