""" My module that does something """


class class1(object):
    """
    This is a class that is a class
    """
    def classfunc1(self, arg1, arg2):
        """Is a class function

        Parameters:
          arg1 (int): an integer argument
          arg2 (str): a string argument
  
        Returns:
          str: A concatenation of arg1 and arg2
        """

        return str(arg1) + " " + arg2


def func1(arg1=0, arg2=0):
    """ This is a function that is a function

    Parameters:
      arg1 (int): an integer argument
      arg2 (int): a second integer argument

    Returns:
      str: the sum of the arguments
    """

    return arg1 + arg2
