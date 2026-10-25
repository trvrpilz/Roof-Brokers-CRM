# Roof Brokers iPhone App

This folder contains the native SwiftUI iPhone shell for the Roof Brokers CRM.

## Current behavior

- Opens the secured Roof Brokers CRM at `https://roof-brokers-api-staging.up.railway.app/`.
- Uses persistent WKWebView website data so the existing secure browser session/cookie flow works on iPhone.
- Keeps authorization on the server. Owner sees all company leads; non-owner users only receive leads assigned to their own user ID.
- Opens `tel:`, `sms:` and `mailto:` actions in the corresponding iOS apps.
- Supports camera/media capture for inspection photos.
- Includes camera, photo library and when-in-use location permission descriptions.
- Targets iPhone on iOS 15 or newer.

## Open in Xcode

Open `ios/RoofBrokers.xcodeproj` in Xcode.

Under **Roof Brokers > Signing & Capabilities**:

1. Select the Apple Developer Team that will publish Roof Brokers.
2. Confirm or change the bundle identifier (`com.roofbrokers.crm`) if necessary.
3. Leave signing set to Automatic.

The app can then be run on a connected iPhone or simulator.

## TestFlight

Before App Store Connect upload:

1. Add the final 1024x1024 Roof Brokers app icon to `RoofBrokers/Assets.xcassets/AppIcon.appiconset`.
2. In Xcode choose **Product > Archive** using a physical-device destination.
3. In Organizer choose **Distribute App > App Store Connect > Upload**.
4. In App Store Connect add the build to TestFlight and invite testers.

No API keys or CRM passwords are stored in the iOS source. Authentication continues to be handled by the deployed backend.
