// spotify-tap — record a single app's audio (Spotify) via Core Audio process taps.
//
// macOS 14.4+ added AudioHardwareCreateProcessTap, which taps the audio stream of
// specific processes. We tap every process whose bundle id starts with a given
// prefix (default com.spotify), mix to stereo, and write to a WAV until SIGINT/SIGTERM.
//
// Because it taps Spotify specifically, NOTHING ELSE bleeds in — no notifications,
// no other apps — and playback to the speakers continues normally (mute = .unmuted).
//
// Usage: spotify-tap --out /path/to/master.wav [--bundle-prefix com.spotify]
//
// Build: swiftc -O -framework CoreAudio -framework AudioToolbox -o spotify-tap spotify-tap.swift

import Foundation
import CoreAudio
import AudioToolbox
import AppKit

// ---- arg parsing -----------------------------------------------------------
var outPath = ""
var bundlePrefix = "com.spotify"
var listMode = false
var requestPermission = false
do {
    var i = 1
    let a = CommandLine.arguments
    while i < a.count {
        switch a[i] {
        case "--out": i += 1; if i < a.count { outPath = a[i] }
        case "--bundle-prefix": i += 1; if i < a.count { bundlePrefix = a[i] }
        case "--list": listMode = true
        case "--request-permission": requestPermission = true
        default: break
        }
        i += 1
    }
}

func err(_ s: String) { FileHandle.standardError.write((s + "\n").data(using: .utf8)!) }

// Request the kTCCServiceAudioCapture permission via the private TCC SPI (the only
// way to deterministically trigger the system prompt; there is no public API).
// Must run in a GUI login session — launch the .app via `open` so the dialog shows.
func requestAudioCapturePermission() -> Bool {
    guard let handle = dlopen("/System/Library/PrivateFrameworks/TCC.framework/TCC", RTLD_NOW) else {
        err("could not load TCC.framework"); return false
    }
    let service = "kTCCServiceAudioCapture" as CFString
    typealias PreflightT = @convention(c) (CFString, CFDictionary?) -> Int
    if let pf = dlsym(handle, "TCCAccessPreflight") {
        let preflight = unsafeBitCast(pf, to: PreflightT.self)
        let s = preflight(service, nil)   // 0 = granted, 1 = denied, 2 = unknown
        err("preflight status: \(s)")
        if s == 0 { return true }
    }
    guard let rq = dlsym(handle, "TCCAccessRequest") else {
        err("TCCAccessRequest unavailable"); return false
    }
    typealias RequestT = @convention(c) (CFString, CFDictionary?, @escaping @convention(block) (Bool) -> Void) -> Void
    let request = unsafeBitCast(rq, to: RequestT.self)
    var granted = false
    request(service, nil) { ok in
        granted = ok
        CFRunLoopStop(CFRunLoopGetMain())
    }
    CFRunLoopRun()   // keep main runloop alive so the prompt can present
    return granted
}

if requestPermission {
    let ok = requestAudioCapturePermission()
    err(ok ? "AUDIO CAPTURE: GRANTED" : "AUDIO CAPTURE: DENIED")
    exit(ok ? 0 : 1)
}

guard !outPath.isEmpty || listMode else {
    FileHandle.standardError.write("error: --out <path> required\n".data(using: .utf8)!)
    exit(2)
}

func addr(_ selector: AudioObjectPropertySelector,
          _ scope: AudioObjectPropertyScope = kAudioObjectPropertyScopeGlobal,
          _ element: AudioObjectPropertyElement = kAudioObjectPropertyElementMain)
          -> AudioObjectPropertyAddress {
    AudioObjectPropertyAddress(mSelector: selector, mScope: scope, mElement: element)
}

// ---- find Spotify's audio process object(s) --------------------------------
func processObjectList() -> [AudioObjectID] {
    var address = addr(kAudioHardwarePropertyProcessObjectList)
    var dataSize: UInt32 = 0
    guard AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject),
            &address, 0, nil, &dataSize) == noErr else { return [] }
    let count = Int(dataSize) / MemoryLayout<AudioObjectID>.size
    var ids = [AudioObjectID](repeating: 0, count: count)
    guard AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject),
            &address, 0, nil, &dataSize, &ids) == noErr else { return [] }
    return ids
}

func bundleID(of obj: AudioObjectID) -> String? {
    var address = addr(kAudioProcessPropertyBundleID)
    var size = UInt32(MemoryLayout<CFString?>.size)
    var cf: CFString? = nil
    let status = withUnsafeMutablePointer(to: &cf) {
        AudioObjectGetPropertyData(obj, &address, 0, nil, &size, $0)
    }
    guard status == noErr, let cf else { return nil }
    return cf as String
}

func pid(of obj: AudioObjectID) -> pid_t {
    var address = addr(kAudioProcessPropertyPID)
    var p: pid_t = -1
    var size = UInt32(MemoryLayout<pid_t>.size)
    _ = AudioObjectGetPropertyData(obj, &address, 0, nil, &size, &p)
    return p
}

func isRunningOutput(_ obj: AudioObjectID) -> Bool {
    var address = addr(kAudioProcessPropertyIsRunningOutput)
    var v: UInt32 = 0
    var size = UInt32(MemoryLayout<UInt32>.size)
    _ = AudioObjectGetPropertyData(obj, &address, 0, nil, &size, &v)
    return v != 0
}

// ppid lookup via sysctl, to associate Chromium helper processes with the Spotify app
func parentPID(of p: pid_t) -> pid_t {
    var info = kinfo_proc()
    var size = MemoryLayout<kinfo_proc>.stride
    var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, p]
    let r = sysctl(&mib, 4, &info, &size, nil, 0)
    if r == 0 { return info.kp_eproc.e_ppid }
    return -1
}

if listMode {
    let spotifyPIDs = Set(NSWorkspace.shared.runningApplications
        .filter { ($0.bundleIdentifier ?? "").hasPrefix(bundlePrefix) }
        .map { $0.processIdentifier })
    err("Spotify app PIDs: \(spotifyPIDs.sorted())")
    for obj in processObjectList() {
        let p = pid(of: obj)
        let par = parentPID(of: p)
        let related = spotifyPIDs.contains(p) || spotifyPIDs.contains(par)
        print("obj=\(obj) pid=\(p) ppid=\(par) output=\(isRunningOutput(obj)) bundle=\(bundleID(of: obj) ?? "nil") spotify=\(related)")
    }
    exit(0)
}

let matches = processObjectList().filter {
    (bundleID(of: $0)?.lowercased().hasPrefix(bundlePrefix.lowercased())) ?? false
}
guard !matches.isEmpty else {
    err("error: no audio process found with bundle prefix '\(bundlePrefix)'. Is Spotify running and has it played audio this session?")
    exit(3)
}
err("tapping \(matches.count) process object(s) for '\(bundlePrefix)'")

// ---- create the process tap ------------------------------------------------
let tapDesc = CATapDescription(stereoMixdownOfProcesses: matches)
tapDesc.isPrivate = true
tapDesc.muteBehavior = .unmuted   // keep hearing Spotify through the speakers

var tapID = AudioObjectID(0)
var st = AudioHardwareCreateProcessTap(tapDesc, &tapID)
guard st == noErr, tapID != 0 else {
    err("error: AudioHardwareCreateProcessTap failed (\(st)). If this is a permission error, grant audio capture to your terminal in System Settings → Privacy & Security → Screen & System Audio Recording, then retry.")
    exit(4)
}

// tap UID + stream format
func tapUID() -> CFString? {
    var address = addr(kAudioTapPropertyUID)
    var size = UInt32(MemoryLayout<CFString?>.size)
    var cf: CFString? = nil
    let status = withUnsafeMutablePointer(to: &cf) {
        AudioObjectGetPropertyData(tapID, &address, 0, nil, &size, $0)
    }
    return status == noErr ? cf : nil
}
guard let uid = tapUID() else { err("error: could not read tap UID"); exit(5) }

var tapFormat = AudioStreamBasicDescription()
do {
    var address = addr(kAudioTapPropertyFormat)
    var size = UInt32(MemoryLayout<AudioStreamBasicDescription>.size)
    st = AudioObjectGetPropertyData(tapID, &address, 0, nil, &size, &tapFormat)
    guard st == noErr else { err("error: could not read tap format (\(st))"); exit(6) }
}
let channels = max(1, tapFormat.mChannelsPerFrame)
err("tap format: \(Int(tapFormat.mSampleRate)) Hz, \(channels) ch, \(tapFormat.mBitsPerChannel)-bit")

// ---- aggregate device wrapping the tap -------------------------------------
let aggUID = "com.paradisegarage.spotifytap.agg"
let aggDescription: [String: Any] = [
    kAudioAggregateDeviceNameKey as String: "PG Spotify Tap",
    kAudioAggregateDeviceUIDKey as String: aggUID,
    kAudioAggregateDeviceIsPrivateKey as String: true,
    kAudioAggregateDeviceIsStackedKey as String: false,
    kAudioAggregateDeviceTapAutoStartKey as String: true,
    kAudioAggregateDeviceTapListKey as String: [[
        kAudioSubTapUIDKey as String: uid,
        kAudioSubTapDriftCompensationKey as String: true,
    ]],
]
var aggID = AudioObjectID(0)
st = AudioHardwareCreateAggregateDevice(aggDescription as CFDictionary, &aggID)
guard st == noErr, aggID != 0 else {
    err("error: AudioHardwareCreateAggregateDevice failed (\(st))")
    AudioHardwareDestroyProcessTap(tapID)
    exit(7)
}

// ---- output file (Float32 WAV; ffmpeg downstream resamples to 44.1k/16-bit) -
var fileASBD = AudioStreamBasicDescription(
    mSampleRate: tapFormat.mSampleRate,
    mFormatID: kAudioFormatLinearPCM,
    mFormatFlags: kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked,
    mBytesPerPacket: 4 * channels,
    mFramesPerPacket: 1,
    mBytesPerFrame: 4 * channels,
    mChannelsPerFrame: channels,
    mBitsPerChannel: 32,
    mReserved: 0)

var extFile: ExtAudioFileRef? = nil
let url = URL(fileURLWithPath: outPath) as CFURL
st = ExtAudioFileCreateWithURL(url, kAudioFileWAVEType, &fileASBD, nil,
                               AudioFileFlags.eraseFile.rawValue, &extFile)
guard st == noErr, let extFile else {
    err("error: ExtAudioFileCreateWithURL failed (\(st))")
    AudioHardwareDestroyAggregateDevice(aggID)
    AudioHardwareDestroyProcessTap(tapID)
    exit(8)
}
// client format = the tap's native format (ExtAudioFile converts to file format)
st = ExtAudioFileSetProperty(extFile, kExtAudioFileProperty_ClientDataFormat,
                             UInt32(MemoryLayout<AudioStreamBasicDescription>.size), &tapFormat)
guard st == noErr else { err("error: set client format failed (\(st))"); exit(9) }
// prime the async writer (must be called before ExtAudioFileWriteAsync in the IOProc)
ExtAudioFileWriteAsync(extFile, 0, nil)

// ---- IO proc: write tapped audio to disk -----------------------------------
// Pass the ExtAudioFileRef + bytesPerFrame to the C callback via context.
final class Ctx {
    let file: ExtAudioFileRef
    let bytesPerFrame: UInt32
    init(_ f: ExtAudioFileRef, _ bpf: UInt32) { file = f; bytesPerFrame = bpf }
}
let ctx = Ctx(extFile, tapFormat.mBytesPerFrame == 0 ? 4 : tapFormat.mBytesPerFrame)
let ctxPtr = Unmanaged.passRetained(ctx).toOpaque()

let ioProc: AudioDeviceIOProc = { (_, _, inInputData, _, _, _, clientData) -> OSStatus in
    guard let clientData, let input = inInputData as UnsafePointer<AudioBufferList>? else { return noErr }
    let ctx = Unmanaged<Ctx>.fromOpaque(clientData).takeUnretainedValue()
    let firstBuf = input.pointee.mBuffers   // first AudioBuffer
    guard firstBuf.mDataByteSize > 0, ctx.bytesPerFrame > 0 else { return noErr }
    let frames = firstBuf.mDataByteSize / ctx.bytesPerFrame
    if frames > 0 {
        ExtAudioFileWriteAsync(ctx.file, frames, input)
    }
    return noErr
}

var procID: AudioDeviceIOProcID? = nil
st = AudioDeviceCreateIOProcID(aggID, ioProc, ctxPtr, &procID)
guard st == noErr, let procID else {
    err("error: AudioDeviceCreateIOProcID failed (\(st))")
    exit(10)
}
st = AudioDeviceStart(aggID, procID)
guard st == noErr else { err("error: AudioDeviceStart failed (\(st))"); exit(11) }
err("recording → \(outPath)  (SIGINT/SIGTERM to stop)")

// ---- run until signalled ---------------------------------------------------
var running = true
let stop: @convention(c) (Int32) -> Void = { _ in /* set via signal() below */ }
signal(SIGINT) { _ in CFRunLoopStop(CFRunLoopGetMain()) }
signal(SIGTERM) { _ in CFRunLoopStop(CFRunLoopGetMain()) }
_ = stop; _ = running
CFRunLoopRun()   // blocks until a signal handler stops it

// ---- teardown --------------------------------------------------------------
AudioDeviceStop(aggID, procID)
AudioDeviceDestroyIOProcID(aggID, procID)
ExtAudioFileDispose(extFile)
AudioHardwareDestroyAggregateDevice(aggID)
AudioHardwareDestroyProcessTap(tapID)
Unmanaged<Ctx>.fromOpaque(ctxPtr).release()
err("stopped.")
exit(0)
