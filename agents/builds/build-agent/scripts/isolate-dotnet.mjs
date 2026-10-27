// LEGACY one-time migration resource. Current generation uses build/ and .tmp/.
// Materialize project-local .NET dependencies. The resulting projects do not
// need this orchestration script or any sibling source directory to build.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const src=path.join(root,'test-project1/srcs');
const skip=new Set(['bin','obj','build','.vs','node_modules','__pycache__']);
function copy(from,to){if(fs.existsSync(to))throw new Error('Destination exists: '+to);fs.cpSync(from,to,{recursive:true,filter:f=>!f.split(path.sep).some(s=>skip.has(s))});}
const put=(file,text)=>fs.writeFileSync(file,text);
const replace=(file,from,to)=>put(file,fs.readFileSync(file,'utf8').replaceAll(from,to));
for(const way of ['CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI']){
 const project=path.join(src,way);
 copy(path.join(src,'Shared/StudentManagement.Core'),path.join(project,'Core'));
 copy(path.join(src,'Shared/StudentMaintenance'),path.join(project,'maintenance'));
 copy(path.join(src,'Shared/StudentManagement.Core.Tests'),path.join(project,'tests/Core'));
 copy(path.join(src,'Database/SQLServer'),path.join(project,'database'));
 replace(path.join(project,'maintenance/StudentMaintenance.csproj'),'../StudentManagement.Core/','../Core/');
 replace(path.join(project,'tests/Core/StudentManagement.Core.Tests.csproj'),'../StudentManagement.Core/','../../Core/');
 replace(path.join(project,'database/tests/SqlServer.IntegrationTests.csproj'),'../../../Shared/StudentManagement.Core/','../../Core/');
 replace(path.join(project,'database/generate.mjs'),"path.resolve(output,'../../..')","path.resolve(output,'..')");
 replace(path.join(project,'database/generate.mjs'),'student 7.4','student 8.0');
 const main=way==='CSharp_WPF'?'StudentManagement.Wpf.csproj':way==='CSharp_ASPNET'?'StudentManagement.Web.csproj':'backend/StudentManagement.Api.csproj';
 const mainFile=path.join(project,main);let text=fs.readFileSync(mainFile,'utf8');
 text=text.replace(/<ProjectReference Include="[^\"]*Shared[^\"]*"\s*\/>/g,`<ProjectReference Include="${way==='Vue_CSharpAPI'?'../':''}Core/StudentManagement.Core.csproj" />`);
 text=text.replace(/\s*<Compile Include="[^\"]*CSharp_ASPNET[^\"]*"[^>]*\/>/g,'');
 if(way!=='Vue_CSharpAPI')text=text.replace('</Project>','  <ItemGroup><Compile Remove="Core/**/*.cs;maintenance/**/*.cs;database/**/*.cs;tests/**/*.cs;Tests/**/*.cs" /><Content Remove="Core/**/*;maintenance/**/*;database/**/*;tests/**/*;spec/**/*" /><None Remove="Core/**/*;maintenance/**/*;database/**/*;tests/**/*;spec/**/*" /></ItemGroup>\n</Project>');
 put(mainFile,text);
 if(way==='Vue_CSharpAPI'){
  copy(path.join(src,'CSharp_ASPNET/Infrastructure'),path.join(project,'backend/Infrastructure'));
  copy(path.join(src,'CSharp_ASPNET/Web/Inputs'),path.join(project,'backend/Contracts'));
  // API uses controller-only configuration; no sibling MVC views or controllers.
  replace(path.join(project,'backend/Infrastructure/WebHostSetup.cs'),'AddControllersWithViews','AddControllers');
  copy(path.join(src,'CSharp_ASPNET/tests/Program.cs'),path.join(project,'tests/ApiContracts.cs'));
 }
 console.log(JSON.stringify({way,localCore:true,localDatabase:true,localMaintenance:true}));
}
const vb=path.join(src,'VB.NET_WinForms');
fs.mkdirSync(path.join(vb,'build/migration'),{recursive:true});
copy(path.join(src,'Shared/StudentManagement.Core'),path.join(vb,'build/migration/Core'));
copy(path.join(src,'Shared/StudentManagement.Core.Tests'),path.join(vb,'build/migration/Core.Tests'));
copy(path.join(src,'Shared/StudentMaintenance'),path.join(vb,'build/migration/Maintenance'));
copy(path.join(src,'Database/SQLServer'),path.join(vb,'database'));
replace(path.join(vb,'database/generate.mjs'),"path.resolve(output,'../../..')","path.resolve(output,'..')");
replace(path.join(vb,'database/generate.mjs'),'student 7.4','student 8.0');
console.log(JSON.stringify({way:'VB.NET_WinForms',vbMigrationSource:'build/migration',localDatabase:true}));
