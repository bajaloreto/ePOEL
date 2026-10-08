import Foundation
import Vision
import AppKit
let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
let h = VNImageRequestHandler(cgImage: cg, options: [:])
try h.perform([req])
var out: [[String: Any]] = []
for o in req.results ?? [] {
  guard let c = o.topCandidates(1).first else { continue }
  let b = o.boundingBox
  out.append(["texto": c.string, "x": b.origin.x * Double(cg.width), "y": (1 - b.origin.y - b.size.height) * Double(cg.height), "w": b.size.width * Double(cg.width), "h": b.size.height * Double(cg.height), "conf": c.confidence])
}
print(String(data: try JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
