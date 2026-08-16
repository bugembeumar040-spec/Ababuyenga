import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
// Default is 80. The paper grain is fine high-frequency noise — the worst case
// for JPEG — and this is an intermediate the master can never get back.
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
Config.setChromiumOpenGlRenderer("angle");
