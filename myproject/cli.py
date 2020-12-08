import click

from myproject.mymodule import class1, func1


@click.command()
@click.argument('string')
@click.argument('number')
def concatstrnum(string, number):
    """Concatenate a string and a number"""
    c = class1()
    return c.classfunc1(number, string)


@click.command()
@click.argument('num1')
@click.argument('num2')
def addnums(num1, num2):
    """ Add 2 numbers """

    return func1(num1, num2)


@click.group()
@click.option('--verbose', help="verbose output")
def cli(verbose):
    if verbose:
        print("This is verbose")


cli.add_command(concatstrnum)
cli.add_command(addnums)
