using System;
namespace Trial.Business;

public class 登録Service
{
    private readonly Rules rules;
    public 登録Service(Rules rules) { this.rules = rules; }
    public bool Save(string name)
    {
        if (!rules.Allowed(name)) return false;
        return Save(name, 1);
    }
    public bool Save(string name, int count) { return count > 0; }
}

public class OtherService
{
    public bool Save(string name) { return false; }
}
