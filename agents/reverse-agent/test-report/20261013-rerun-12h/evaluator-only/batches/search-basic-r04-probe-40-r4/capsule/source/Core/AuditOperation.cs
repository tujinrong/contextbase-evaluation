namespace StudentManagement.Core;

// COM-STU-003 7.4: name changes on an already stopped master remain UPDATE.
internal static class AuditOperation
{
    internal static string ForMaster(bool? previousActive,bool currentActive)
        => previousActive is null ? "CREATE" : previousActive==currentActive ? "UPDATE" : currentActive ? "ENABLE" : "DISABLE";
}
