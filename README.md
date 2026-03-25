# Domio - Smart Home

A modern iOS app for controlling [Indigo](https://www.indigodomo.com/) home automation systems. Real-time device control, voice commands, push notifications, device history, CarPlay, Apple Watch, and Siri — all in a Liquid Glass interface designed for iOS 26.

> **Domio** is an independent, community-built app. It is **not made by or affiliated with Indigo Domotics.**

[![Download on the App Store](https://developer.apple.com/assets/elements/badges/download-on-the-app-store.svg)](https://apps.apple.com/app/domio-smart-home/id6758682250)

## Device Control

Switches, dimmers, thermostats, sensors, colour lights, fans, and sprinklers — all at your fingertips. Adjust brightness with smooth sliders, set thermostat modes and temperatures, and monitor sensors with battery alerts. Every control responds instantly with haptic feedback.

Tag any device with its actual type — mark a smart plug as "Light" so it appears in the right category and responds to voice commands like "turn off all lights."

## Rooms & Favourites

Organise devices into custom rooms that make sense for your home. Pin your most-used devices and scenes to Favourites for one-tap access. Drag to reorder, long-press to edit — just like your home screen. Export and share room layouts with family members.

## Scenes

Execute any Indigo action group with a single tap. Browse by folder or add to Favourites for quick access.

## Voice Assistant

Speak naturally to control your home. "Turn off the kitchen lights", "Set the heating to 21 degrees", or "What lights are on?" The assistant understands your rooms and devices, asks clarifying questions when needed, and confirms actions in a few words. Works from iPhone, Apple Watch, and CarPlay.

Powered by your choice of AI — Claude, ChatGPT, Grok, or a local model. You provide your own API key.

## Push Notifications

Instant alerts when doors open, temperatures drop, or automations need attention. Tap a notification to jump straight to the device or scene. Silent background pushes keep your widgets fresh. One optional subscription covers your whole family via Family Sharing.

## Device History

Charts of temperature, humidity, energy, and any device state over time — powered by your SQL Logger data. Switch between 1-hour, 6-hour, 24-hour, 7-day, and 30-day views.

## CarPlay

Control your home from the car. Run scenes like "I'm Home" as you pull into the driveway. Toggle lights and devices. Voice control works hands-free.

## Home Screen Widgets

Keep an eye on your home without opening the app. Four widget types in small and medium sizes:

- **Device Status** (small) — single device with live state
- **Variable Value** (small) — single variable name and value
- **Device Grid** (medium) — 2×2 overview of your chosen devices
- **Device Detail** (medium) — rich single-device view for thermostats, dimmers, and relays

Widgets update automatically in the background. Tap any widget to jump into the app.

## Apple Watch

Toggle devices, run scenes, and use voice control from your wrist.

## Siri & Shortcuts

Works with Siri out of the box. "Hey Siri, Indigo turn on the porch light" or "Indigo run movie time." Fully integrated with the Shortcuts app for building your own automations.

## Event Log

View your Indigo event log in real time or browse historical entries by date. Filter by source, severity, or search for specific events. Enable the debug log to see push delivery, connection events, and app diagnostics.

## Browse & Search

Search across all devices, scenes, and variables from one unified view. Category pills give quick access to all lights, thermostats, sensors, or security devices. Everything organised by your Indigo folder structure with collapsible sections.

## Secure & Private

Credentials stored in the iOS Keychain. Remote connections encrypted via Indigo Reflector (TLS). Local network mode available for on-premise control. No tracking, no analytics, no third-party services.

## Designed for iOS 26

Built entirely with SwiftUI and the Liquid Glass design language. Four colour themes. Light and dark mode. Full VoiceOver, Dynamic Type, and high contrast accessibility support.

## Try Before You Connect

Enter Demo Mode to explore the full app with sample data — no Indigo server required.

## Requirements

- iOS 18 or later (iPhone and iPad). Optimised for iOS 26.
- An [Indigo](https://www.indigodomo.com/) home automation server with Reflector access or local network connectivity
- Push notifications require an optional subscription

## Support

- **App issues** (bugs, crashes, feature requests): [Open an issue](https://github.com/simons-plugins/Domio-Smart-Home/issues)
- **Indigo server/plugin issues** (devices not responding, automation problems, plugin errors): Please visit the [Indigo Domotics Community Forums](https://forums.indigodomo.com/)

## Privacy

This app does not collect, store, or transmit any personal data. See our [Privacy Policy](https://simons-plugins.github.io/Domio-Smart-Home/privacy.html).
