#include <wayland-client.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static FILE *output;
static int received;

static void keyboard_keymap(void *data, struct wl_keyboard *keyboard, uint32_t format,
                            int fd, uint32_t size) {
    (void)data; (void)keyboard;
    if (format != WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1) { close(fd); return; }
    char buffer[4096];
    ssize_t count;
    while ((count = read(fd, buffer, sizeof(buffer))) > 0)
        if (fwrite(buffer, 1, (size_t)count, output) != (size_t)count) exit(1);
    close(fd);
    received = size > 0 && count == 0;
}
static void keyboard_enter(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                           struct wl_surface *surface, struct wl_array *keys) {
    (void)data; (void)keyboard; (void)serial; (void)surface; (void)keys;
}
static void keyboard_leave(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                           struct wl_surface *surface) {
    (void)data; (void)keyboard; (void)serial; (void)surface;
}
static void keyboard_key(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                         uint32_t time, uint32_t key, uint32_t state) {
    (void)data; (void)keyboard; (void)serial; (void)time; (void)key; (void)state;
}
static void keyboard_modifiers(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                               uint32_t depressed, uint32_t latched, uint32_t locked,
                               uint32_t group) {
    (void)data; (void)keyboard; (void)serial; (void)depressed; (void)latched;
    (void)locked; (void)group;
}
static void keyboard_repeat(void *data, struct wl_keyboard *keyboard, int32_t rate,
                            int32_t delay) {
    (void)data; (void)keyboard; (void)rate; (void)delay;
}
static const struct wl_keyboard_listener keyboard_listener = {
    keyboard_keymap, keyboard_enter, keyboard_leave, keyboard_key,
    keyboard_modifiers, keyboard_repeat
};
static void seat_capabilities(void *data, struct wl_seat *seat, uint32_t capabilities) {
    (void)data;
    if (capabilities & WL_SEAT_CAPABILITY_KEYBOARD) {
        struct wl_keyboard *keyboard = wl_seat_get_keyboard(seat);
        wl_keyboard_add_listener(keyboard, &keyboard_listener, NULL);
    }
}
static void seat_name(void *data, struct wl_seat *seat, const char *name) {
    (void)data; (void)seat; (void)name;
}
static const struct wl_seat_listener seat_listener = { seat_capabilities, seat_name };
static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version) {
    (void)data;
    if (strcmp(interface, wl_seat_interface.name) == 0) {
        struct wl_seat *seat = wl_registry_bind(registry, name, &wl_seat_interface,
                                               version < 5 ? version : 5);
        wl_seat_add_listener(seat, &seat_listener, NULL);
    }
}
static void global_remove(void *data, struct wl_registry *registry, uint32_t name) {
    (void)data; (void)registry; (void)name;
}
static const struct wl_registry_listener registry_listener = { global, global_remove };

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    output = fopen(argv[1], "wb");
    if (!output) return 1;
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) return 1;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    for (int i = 0; i < 5 && !received; ++i)
        if (wl_display_roundtrip(display) < 0) break;
    wl_display_disconnect(display);
    fclose(output);
    if (!received) fprintf(stderr, "Wayland compositor did not send a keyboard keymap.\n");
    return !received;
}
