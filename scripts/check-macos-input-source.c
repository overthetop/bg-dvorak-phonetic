#include <Carbon/Carbon.h>
#include <stdio.h>
#include <string.h>

static int check_key(const UCKeyboardLayout *layout, UInt16 key, UInt32 modifiers,
                     UniChar expected) {
    UInt32 dead = 0;
    UniChar value[4];
    UniCharCount length = 0;
    OSStatus status = UCKeyTranslate(layout, key, kUCKeyActionDown, modifiers,
                                    LMGetKbdType(), kUCKeyTranslateNoDeadKeysMask,
                                    &dead, 4, &length, value);
    if (status != noErr || length != 1 || value[0] != expected) {
        fprintf(stderr, "macOS key %u produced an unexpected character (status %d).\n",
                key, (int)status);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    CFURLRef url = CFURLCreateFromFileSystemRepresentation(NULL,
        (const UInt8 *)argv[1], strlen(argv[1]), true);
    if (!url) return 1;
    OSStatus status = TISRegisterInputSource(url);
    CFRelease(url);
    if (status != noErr) {
        fprintf(stderr, "TISRegisterInputSource failed: %d\n", (int)status);
        return 1;
    }
    CFStringRef source_id = CFSTR("org.sil.ukelele.keyboardlayout.bg-dvorak-phonetic.bg-dvorak-phonetic");
    const void *keys[] = { kTISPropertyInputSourceID };
    const void *values[] = { source_id };
    CFDictionaryRef filter = CFDictionaryCreate(NULL, keys, values, 1,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);
    CFArrayRef sources = TISCreateInputSourceList(filter, true);
    CFRelease(filter);
    if (!sources || CFArrayGetCount(sources) != 1) {
        fprintf(stderr, "macOS did not discover the registered input source (matching count: %ld).\n",
                sources ? (long)CFArrayGetCount(sources) : -1L);
        CFArrayRef all = TISCreateInputSourceList(NULL, true);
        if (all) {
            for (CFIndex i = 0; i < CFArrayGetCount(all); ++i) {
                TISInputSourceRef item = (TISInputSourceRef)CFArrayGetValueAtIndex(all, i);
                CFStringRef id = TISGetInputSourceProperty(item, kTISPropertyInputSourceID);
                if (id && CFStringFind(id, CFSTR("bg-dvorak"), kCFCompareCaseInsensitive).location != kCFNotFound)
                    CFShow(id);
            }
            CFRelease(all);
        }
        if (sources) CFRelease(sources);
        return 1;
    }
    TISInputSourceRef source = (TISInputSourceRef)CFArrayGetValueAtIndex(sources, 0);
    CFDataRef data = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData);
    if (!data || CFDataGetLength(data) < sizeof(UCKeyboardLayout)) {
        fprintf(stderr, "macOS input source has no Unicode keyboard layout data.\n");
        CFRelease(sources);
        return 1;
    }
    const UCKeyboardLayout *layout = (const UCKeyboardLayout *)CFDataGetBytePtr(data);
    int failed = check_key(layout, 1, 0, 0x043e) ||
                 check_key(layout, 7, 0, 0x044f) ||
                 check_key(layout, 13, 0, ',') ||
                 check_key(layout, 7, shiftKey >> 8, 0x042f);
    CFRelease(sources);
    if (!failed) puts("macOS discovered the input source and translated representative keys.");
    return failed;
}
