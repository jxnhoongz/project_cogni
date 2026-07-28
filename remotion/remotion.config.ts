import { Config } from "@remotion/cli/config";

// Throwaway spike config. JPEG frames render faster; good enough for a POC.
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
