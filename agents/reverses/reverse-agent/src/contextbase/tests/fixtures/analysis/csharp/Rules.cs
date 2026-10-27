namespace Trial.Business
{
    public class Rules
    {
        public bool Allowed(string name) { return name != null && name.Length > 0; }
    }
}
