#import "VisionBridge.h"

#import <Foundation/Foundation.h>
#import <Vision/Vision.h>
#import <math.h>

CFDataRef _Nullable FSCreateFeaturePrintArchive(
    CGImageRef image,
    CFErrorRef _Nullable * _Nullable error
) {
    VNGenerateImageFeaturePrintRequest *request = [[VNGenerateImageFeaturePrintRequest alloc] init];
    if (@available(macOS 14.0, *)) {
        request.revision = VNGenerateImageFeaturePrintRequestRevision2;
    } else {
        request.revision = VNGenerateImageFeaturePrintRequestRevision1;
    }
    VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:image options:@{}];

    NSError *requestError = nil;
    if (![handler performRequests:@[request] error:&requestError]) {
        if (error != NULL) {
            *error = (CFErrorRef)CFBridgingRetain(requestError);
        }
        return NULL;
    }

    VNFeaturePrintObservation *observation =
        (VNFeaturePrintObservation *)request.results.firstObject;
    if (observation == nil) {
        if (error != NULL) {
            NSError *missingResult = [NSError errorWithDomain:@"FinderSight.VisualFeature"
                                                         code:1
                                                     userInfo:@{
                NSLocalizedDescriptionKey: @"Vision did not return a feature print."
            }];
            *error = (CFErrorRef)CFBridgingRetain(missingResult);
        }
        return NULL;
    }

    NSError *archiveError = nil;
    NSData *archive = [NSKeyedArchiver archivedDataWithRootObject:observation
                                           requiringSecureCoding:YES
                                                           error:&archiveError];
    if (archive == nil) {
        if (error != NULL) {
            *error = (CFErrorRef)CFBridgingRetain(archiveError);
        }
        return NULL;
    }
    return CFBridgingRetain(archive);
}

float FSMinimumFeaturePrintDistance(
    CFDataRef queryArchive,
    CFArrayRef candidateArchives
) {
    NSError *queryError = nil;
    VNFeaturePrintObservation *query = [NSKeyedUnarchiver
        unarchivedObjectOfClass:VNFeaturePrintObservation.class
        fromData:(__bridge NSData *)queryArchive
        error:&queryError];
    if (query == nil) {
        return NAN;
    }

    float best = INFINITY;
    for (NSData *archive in (__bridge NSArray<NSData *> *)candidateArchives) {
        NSError *candidateError = nil;
        VNFeaturePrintObservation *candidate = [NSKeyedUnarchiver
            unarchivedObjectOfClass:VNFeaturePrintObservation.class
            fromData:archive
            error:&candidateError];
        if (candidate == nil) {
            continue;
        }

        float distance = 0;
        NSError *distanceError = nil;
        if ([query computeDistance:&distance
        toFeaturePrintObservation:candidate
                            error:&distanceError] && distance < best) {
            best = distance;
        }
    }
    return isfinite(best) ? best : NAN;
}
