using System;

public static class InputRules
{
    private static string Normalize(string value)
    {
        return value.Trim();
    }

    public static string PrepareA(string value)
    {
        Normalize(value);
        return value;
    }

    public static string PrepareB(string value)
    {
        value = Normalize(value);
        return value;
    }

    public static bool CheckA(string value)
    {
        return value.Length <= 8;
    }

    public static bool CheckB(string value)
    {
        return value.Length < 8;
    }

    public static int ReadA(string value)
    {
        try
        {
            return int.Parse(value);
        }
        catch (FormatException)
        {
            return -1;
        }
    }

    public static int ReadB(string value)
    {
        try
        {
            return int.Parse(value);
        }
        catch (FormatException)
        {
            return -1;
        }
        catch (OverflowException)
        {
            return -2;
        }
    }
}
