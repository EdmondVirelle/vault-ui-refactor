import { describe, expect, it } from "vitest";
import { isValidPathFormat } from "./path";

describe("isValidPathFormat", () => {
  it("accepts windows drive absolute path", () => {
    expect(isValidPathFormat("C:\\Consilience\\scripts")).toBe(true);
  });

  it("accepts UNC path", () => {
    expect(isValidPathFormat("\\\\server\\share\\project")).toBe(true);
  });

  it("accepts unix absolute path", () => {
    expect(isValidPathFormat("/opt/consilience")).toBe(true);
  });

  it("rejects relative path", () => {
    expect(isValidPathFormat("scripts/output")).toBe(false);
  });
});
