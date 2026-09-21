#define GNOME_DESKTOP_USE_UNSTABLE_API
#include <libgnome-desktop/gnome-xkb-info.h>
#include <glib.h>
#include <string.h>

int main(void) {
    GnomeXkbInfo *info = gnome_xkb_info_new();
    const char *display = NULL, *short_name = NULL, *layout = NULL, *variant = NULL;
    gboolean found = gnome_xkb_info_get_layout_info(info, "bgdv", &display,
                                                     &short_name, &layout, &variant);
    if (!found || !layout || strcmp(layout, "bgdv") != 0 ||
        !display || !strstr(display, "Dvorak phonetic")) {
        g_printerr("GNOME did not discover the installed bgdv layout.\n");
        g_object_unref(info);
        return 1;
    }
    g_print("GNOME discovered %s (XKB %s).\n", display, layout);
    g_object_unref(info);
    return 0;
}
