#ifndef VisionBridge_h
#define VisionBridge_h

#include <CoreFoundation/CoreFoundation.h>
#include <CoreGraphics/CoreGraphics.h>

CF_ASSUME_NONNULL_BEGIN

CFDataRef _Nullable FSCreateFeaturePrintArchive(
    CGImageRef image,
    CFErrorRef _Nullable * _Nullable error
) CF_RETURNS_RETAINED;

float FSMinimumFeaturePrintDistance(
    CFDataRef queryArchive,
    CFArrayRef candidateArchives
);

CF_ASSUME_NONNULL_END

#endif
