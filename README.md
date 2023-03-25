# What is that?

`Bulgarian Dvorak Phonetic Keyboard Layout`

This is a traditional bulgarian dvorak keyboard layout that maps the `US Dvorak` keys to the `Bulgarian Cyrillic` alphabet.

Dvorak is an alternative typing layout for English based languages. It is one of the most popular alternative layouts and if you have invested into Dvorak and haven't maintained your Qwerty touchtyping it can be quite awkward to go back.

Cyrillic Phonetic is a keyboard layout that is designed to make typing Cyrillic for native english speakers easier, by transliterating (finding similar sounds and letters across both languages) the keys. This often makes learning to type Cyrillic easier for English speakers because it doesn't require memorizing a completly new layout that is the typical Cyrillic layout.

Linux Layout
![alt text](https://github.com/overthetop/bg-dvorak-phonetic/blob/main/linux/layout.jpg?raw=true)

Mac OS Layout
![alt text](https://github.com/overthetop/bg-dvorak-phonetic/blob/main/mac-os/layout.jpg?raw=true)

# Instalation Mac OS
 
 - Clone this git repository on your local computer `git clone --depth 1 --branch v1.0.0 https://github.com/overthetop/bg-dvorak-phonetic.git`
 - Copy /mac-os/bg-dvorak-phonetic.bundle dir into ~/Library/Keyboard Layouts
 - Go to System Settings -> Keyboard on your Mac machine and hit the + button
 - Select your layout `bg-dvorak-phonetic` from the list and add it
 - You should be able to switch layouts with `^ + Space` shortcut and use it right away 

# Installation Linux

 - Clone this git repository on your local computer `git clone --depth 1 --branch v1.0.0 https://github.com/overthetop/bg-dvorak-phonetic.git`
 - Append all the contents of `symbols-bg-dv` file in the end of `/usr/share/X11/xkb/symbols/bg` file of your Linux distro
 - Insert all the contents of `evdev.xml` under `configItem > bg > variantList` element of `/usr/share/X11/xkb/rules/evdev.xml` file:
    
    ```xml
    <layout>
    <configItem>
        <name>bg</name>
        <!-- Keyboard indicator for Bulgarian layouts -->
        <shortDescription>bg</shortDescription>
        <description>Bulgarian</description>
        <languageList>
        <iso639Id>bul</iso639Id>
        </languageList>
    </configItem>
    <variantList>
        <variant>
        <configItem>
            <name>bg-dvorak-phonetic</name>
            <description>Bulgarian (Dvorak phonetic)</description>
        </configItem>
        </variant>
        <!--more variants follow ... -->
    </variantList>
    ```

 - Reboot or `sudo systemctl restart display-manager` (warning: closes everything!)
 - If you'd like, you can fiddle a bit with it, so run `setxkbmap -layout bg-dvorak-phonetic` to reload changes

