# Roof Brokers iPhone App

This folder contains the native SwiftUI shell for the Roof Brokers CRM.

## What it does

- Runs as an iPhone app using SwiftUI and WKWebView.
- Connects to the existing secure Roof Brokers CRM backend at `https://roof-brokers-api-staging.up.railway.app/`.
- Reuses the existing authenticated CRM workflow, including the five-stage pipeline: Lead, Prospect, Approved, Completed, Invoiced.
- Supports phone/SMS links and requests iPhone permissions needed for field camera, photos, and location workflows.

## Build

1. Install Xcode 16 or newer.
2. Install XcodeGen (`brew install xcodegen`).
3. From this `ios` directory run `xcodegen generate`.
4. Open `RoofBrokers.xcodeproj` in Xcode.
5. Select your Apple Development Team under Signing & Capabilities.
6. Run on an iPhone or Simulator.

## Distribution

Once an Apple Developer account/team is selected in Xcode, this project can be archived for TestFlight and App Store Connect. Before public App Store submission, replace the staging backend URL with the production CRM URL and add final app icons/branding assets.
