# TestFlight checklist

- Open `RoofBrokers.xcodeproj` in Xcode.
- Select the Apple Developer Team under Signing & Capabilities.
- Confirm the bundle identifier is available in the Apple Developer account.
- Add the final 1024x1024 app icon.
- Run on a physical iPhone and verify login, lead list, lead detail, camera/photo upload, field map, call/text links, and logout.
- Test with an Owner account and a non-owner test account to verify lead isolation.
- Archive the Release configuration.
- Upload through Xcode Organizer to App Store Connect.
- Add the build to TestFlight and invite testers.
