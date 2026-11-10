// YTSage PortableApps launcher - transparent Windows PE program (C++17).
// Copyright 2026 Portable kit contributors. MIT. Not affiliated with oop7.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <filesystem>
#include <string>
#include <vector>
#include <cwchar>
#include <cwctype>
#include <cstdint>
#include <sstream>
#include <iomanip>
namespace fs = std::filesystem;
static void fail(const std::wstring &text) {
    MessageBoxW(nullptr, text.c_str(), L"YTSage Portable - Startup Error", MB_OK | MB_ICONERROR);
}
static std::wstring quote(const std::wstring &s) {
    std::wstring out = L"\""; size_t bs=0;
    for (wchar_t c : s) {
        if (c==L'\\') { ++bs; continue; }
        if (c==L'"') { out.append(bs*2+1,L'\\'); out.push_back(L'"'); bs=0; continue; }
        out.append(bs,L'\\'); bs=0; out.push_back(c);
    }
    out.append(bs*2,L'\\'); out.push_back(L'"'); return out;
}
static std::wstring errorText(DWORD code) {
    wchar_t* msg=nullptr;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_FROM_SYSTEM|FORMAT_MESSAGE_IGNORE_INSERTS,
      nullptr,code,0,(LPWSTR)&msg,0,nullptr);
    std::wstring out=msg?msg:L"Unknown Windows error";
    if (msg) LocalFree(msg);
    return out;
}
static bool env(const wchar_t* name, const std::wstring& val) { return SetEnvironmentVariableW(name,val.c_str())!=0; }
static std::wstring getenvstr(const wchar_t* name) {
    DWORD n=GetEnvironmentVariableW(name,nullptr,0);
    if (!n) return L"";
    std::wstring s(n,L'\0'); DWORD actual=GetEnvironmentVariableW(name,s.data(),n);
    if (!actual || actual>=n) return L"";
    s.resize(actual); return s;
}
static unsigned long long rootHash(const std::wstring &value) {
    unsigned long long h=14695981039346656037ull;
    for(wchar_t c : value) {
        wchar_t lc=static_cast<wchar_t>(towlower(c));
        h^=static_cast<unsigned long long>(lc);
        h*=1099511628211ull;
    } return h;
}
int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    wchar_t self[MAX_PATH];
    DWORD n=GetModuleFileNameW(nullptr,self,MAX_PATH);
    if(n==0 || n>=MAX_PATH) { fail(L"Portable path exceeds legacy MAX_PATH or could not be read. Move the folder to a shorter path."); return 2; }
    const fs::path root=fs::path(self).parent_path();
    const fs::path app=root/L"App"/L"YTSage";
    const fs::path data=root/L"Data";
    const fs::path local=data/L"LocalAppData";
    const fs::path download=data/L"Downloads";
    const fs::path deno=data/L"DenoCache";
    const fs::path exe=app/L"YTSage.exe";
    const fs::path ffmpeg=app/L"ffmpeg.exe", ffprobe=app/L"ffprobe.exe";
    if (!fs::is_regular_file(exe) || !fs::is_regular_file(ffmpeg) || !fs::is_regular_file(ffprobe)) {
        fail(L"The official YTSage executable, ffmpeg.exe or ffprobe.exe is missing. Re-extract a verified package without deleting Data.");
        return 3;
    }
    try {
        fs::create_directories(local/L"YTSage"/L"data");
        fs::create_directories(local/L"YTSage"/L"bin");
        fs::create_directories(local/L"YTSage"/L"logs");
        fs::create_directories(download);
        fs::create_directories(deno);
    } catch (const std::exception&) { fail(L"Cannot create portable Data folders. Check drive permissions and available space."); return 4; }
    std::wostringstream name;
    name << L"Local\\YTSagePortable_" << std::hex << rootHash(root.wstring());
    HANDLE mutex=CreateMutexW(nullptr,TRUE,name.str().c_str());
    if(!mutex) { fail(L"Unable to establish the portable instance lock."); return 5; }
    if(GetLastError()==ERROR_ALREADY_EXISTS) { fail(L"This portable YTSage folder is already running. Close it first."); CloseHandle(mutex); return 6; }
    // Child-only changes. No registry writes and no permanent changes to system/User PATH.
    std::wstring path=app.wstring()+L";"+getenvstr(L"PATH");
    if(!env(L"LOCALAPPDATA",local.wstring()) || !env(L"YTSAGE_DOWNLOAD_PATH",download.wstring()) ||
       !env(L"YTSAGE_DOWNLOAD_DIR",download.wstring()) || !env(L"DENO_DIR",deno.wstring()) || !env(L"PATH",path)) {
        fail(L"Unable to prepare child-only portable environment."); ReleaseMutex(mutex);CloseHandle(mutex);return 7;
    }
    int argc=0; LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(!argv) { fail(L"Cannot parse command-line arguments."); ReleaseMutex(mutex);CloseHandle(mutex);return 8; }
    std::wstring command=quote(exe.wstring());
    for(int i=1;i<argc;i++) { command+=L" "; command+=quote(argv[i]); }
    LocalFree(argv);
    std::vector<wchar_t> mutableCmd(command.begin(),command.end()); mutableCmd.push_back(0);
    STARTUPINFOW si{}; si.cb=sizeof(si);
    PROCESS_INFORMATION pi{};
    // A job tracks descendants (yt-dlp, Deno, FFmpeg) to avoid declaring exit too early.
    // No KILL_ON_JOB_CLOSE: unexpected launcher termination must not kill an active download.
    HANDLE job=CreateJobObjectW(nullptr,nullptr);
    BOOL started=CreateProcessW(exe.c_str(),mutableCmd.data(),nullptr,nullptr,FALSE,
                                 CREATE_SUSPENDED, nullptr,app.c_str(),&si,&pi);
    if(!started) {
        fail(L"Could not launch YTSage: "+errorText(GetLastError()));
        if(job)CloseHandle(job);ReleaseMutex(mutex);CloseHandle(mutex);return 9;
    }
    bool tracked=(job!=nullptr && AssignProcessToJobObject(job,pi.hProcess)!=0);
    ResumeThread(pi.hThread); CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess,INFINITE);
    DWORD exitCode=0;GetExitCodeProcess(pi.hProcess,&exitCode);
    // All job-member children must finish before this launcher exits.
    // If Windows prevents job assignment, fall back to waiting only for the GUI.
    if(tracked) {
        for (;;) {
            JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info{};
            if(!QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&info,sizeof(info),nullptr))break;
            if(info.ActiveProcesses==0)break;
            Sleep(500);
        }
    }
    CloseHandle(pi.hProcess); if(job)CloseHandle(job);
    ReleaseMutex(mutex);CloseHandle(mutex);
    return static_cast<int>(exitCode);
}
