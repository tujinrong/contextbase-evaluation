using System.Text.Json;
using System.Security.Cryptography;
using CareerManagement.Application;
using CareerManagement.Infrastructure.State;

var results=new List<object>();var failures=0;
void Check(string id,Action test){try{test();results.Add(new{id,status="PASS"});Console.WriteLine("PASS "+id);}catch(Exception e){failures++;results.Add(new{id,status="FAIL",error=e.Message});Console.WriteLine("FAIL "+id+" "+e.Message);}}
void Assert(bool value){if(!value)throw new InvalidOperationException("Assertion failed");}
void Message(int id,Action action){try{action();throw new Exception("Expected rejection");}catch(BusinessException e){Assert(e.Outcome.MessageId==$"MSG-{id:000}");}}
var time=new ManualTime();var clock=new BusinessClock(time);var store=new ScreenStateStore(clock);
Check("RAW-ORDINAL-INVALIDATION",()=>{
 var s=store.Add(new SearchState("A"){Valid=true,Status=ResultStatus.Success,Applied=new(null,null,null,"01"),Selection=1,Rows=[new(1,"000001","a","ア","開発","在職",new(2020,1,1))]});
 var raw=new SearchRaw("12x"," name "," ZZ ","");ScreenStateStore.CaptureRaw(s,raw,1,42.5);
 Assert(s.Raw==raw&&s.Status==ResultStatus.Unapplied&&!s.Valid&&s.Rows.Count==0&&s.Selection is null&&s.Applied is not null);
 Message(8,()=>ScreenStateStore.CaptureRaw(s,raw,0,0));Assert(s.Raw==raw);
});
Check("IMMUTABLE-SEARCH-COPY",()=>{
 var source=store.Add(new SearchState("A"));source.Raw=new(""," 佐藤 ","02","");source.Status=ResultStatus.Unapplied;source.ScrollTop=18;var reference=store.Checkpoint(source);
 var snapshot=store.ReadResume(reference,source.TabId,"A");var target=store.Add(new SearchState("A"));ScreenStateStore.Restore(target,snapshot);store.Checkpoint(target);
 target.Raw=new("other","","","");Assert(source.Raw.Name==" 佐藤 "&&snapshot.Raw.Name==" 佐藤 "&&target.Id!=source.Id&&target.ResumeRef!=reference&&source.LeaseActive);
 Message(3,()=>store.ReadResume(reference,source.TabId,"B"));
});
Check("ONE-USE-TICKET-OLD-LEASE",()=>{
 var source=store.Add(new NavigationState("A"));var target=store.Add(new NavigationState("A"));var url=store.IssueTicket(source,target,"/menu");var ticket=url.Split('=')[1];
 var consumed=store.Consume<NavigationState>(ticket,"A","/menu");Assert(consumed.Id==target.Id&&!source.LeaseActive&&target.LeaseActive);
 Message(41,()=>store.Consume<NavigationState>(ticket,"A","/menu"));Message(41,()=>store.CheckUi(source,source.Revision,source.TabId,source.DocumentLease));
});
Check("TICKET-60-SECOND-BOUNDARY",()=>{
 var source=store.Add(new NavigationState("A"));source.CommitState=CommitState.Committed;var target=store.Add(new NavigationState("A"));var ticket=store.IssueTicket(source,target,"/menu").Split('=')[1];time.Advance(TimeSpan.FromSeconds(60));
 try{store.Consume<NavigationState>(ticket,"A","/menu");throw new Exception("Expected expiry");}catch(BusinessException e){Assert(e.Outcome.CommitState==CommitState.Committed&&e.Outcome.Message.Contains(Messages.Get(14))&&e.Outcome.Message.Contains(Messages.Get(41)));}
});
Check("UNKNOWN-NEVER-ISSUES-TICKET",()=>{
 var source=store.Add(new NavigationState("A"));source.CommitState=CommitState.Unknown;var target=store.Add(new NavigationState("A"));
 Message(34,()=>store.IssueTicket(source,target,"/menu"));Message(3,()=>store.CheckUi(source,1,"other",source.DocumentLease));
});
Check("DISCARD-BOUND-ACTION-RAW-ONCE",()=>{
 var s=store.Add(new EditState("A","",null,EmployeeRaw.Empty(new(2026,10,30))));
 RawUiEnvelope Raw()=>new(s.Id,s.Revision,s.TabId,s.DocumentLease,s.Employee,s.Pending,null,s.ActiveTab,s.Selected);
 Assert(store.ConfirmLeave(s,Raw(),"Cancel","Search",null,null)==true);
 s.Employee=s.Employee with{Name="unfinished"};Assert(store.ConfirmLeave(s,Raw(),"Cancel","Search",null,null) is null);var id=s.LeaveConfirmation!.Id;
 Message(8,()=>store.ConfirmLeave(s,Raw(),"Navigate","Home",id,DiscardChoice.Discard));
 Assert(store.ConfirmLeave(s,Raw(),"Cancel","Search",id,DiscardChoice.Continue)==false&&s.Employee.Name=="unfinished");
 Message(8,()=>store.ConfirmLeave(s,Raw(),"Cancel","Search",id,DiscardChoice.Discard));
});
Check("RESERVATION-IS-DIRTY",()=>{
 var s=store.Add(new EditState("A","",null,EmployeeRaw.Empty(new(2026,10,30))));Assert(!s.Dirty);s.Pending=CareerRaw.Empty();s.Selected=s.Pending.ClientRowKey;Assert(s.Dirty);
});
Check("STATE-EXPIRY-OPERATION-SWEEP",()=>{
 var old=store.Add(new SearchState("A"));time.Advance(TimeSpan.FromMinutes(30));store.Add(new NavigationState("A"));Message(41,()=>store.Get<SearchState>(old.Id,"A"));
});
Check("SESSION-EXACT-THIRTY-MINUTES",()=>{
 var sessions=new SessionRegistry(clock);var id=sessions.Create("USER");time.Advance(TimeSpan.FromMinutes(29));Assert(sessions.IsValid(id,"USER"));time.Advance(TimeSpan.FromMinutes(1));Assert(!sessions.IsValid(id,"USER")&&!sessions.Touch(id,"USER"));
});
Check("RAW-TECHNICAL-LIMITS-NOT-BUSINESS",()=>{
 Validation.TechnicalRaw(new SearchRaw("partial-invalid"," padded "," unknown ",""));Validation.TechnicalRaw(new string('x',16384));
 try{Validation.TechnicalRaw(new string('x',16385));throw new Exception("Expected length rejection");}catch(ArgumentException){}
 try{Validation.TechnicalRaw("\ud800");throw new Exception("Expected encoding rejection");}catch(ArgumentException){}
 var input=new SearchInput("",1,"12x",null,null,null);Message(5,()=>Validation.Search(input));
});
var root=Environment.CurrentDirectory;var artifact=typeof(ScreenStateStore).Assembly.Location;
var record=new{runId="sp2-ui-regenerate-20261029",scope="State/key/immutable-copy/technical-boundary unit tests; not browser/HTTP/DB acceptance",results,failures,assemblySha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(artifact))),sourceSha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(Path.Combine(root,"tests/UiStateTests/Program.cs"))))};
Directory.CreateDirectory(Path.Combine(root,"build/test-results"));File.WriteAllText(Path.Combine(root,"build/test-results/ui-state-unit.json"),JsonSerializer.Serialize(record,new JsonSerializerOptions{WriteIndented=true})+"\n");return failures==0?0:1;

sealed class ManualTime:TimeProvider
{
 private DateTimeOffset now=new(2026,10,29,15,0,0,TimeSpan.Zero);public override DateTimeOffset GetUtcNow()=>now;public void Advance(TimeSpan value)=>now+=value;
}
