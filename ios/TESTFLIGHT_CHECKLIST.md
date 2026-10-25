# TestFlight checklist

- Open `RoofBrokers.xcodeproj` in Xcode.
- Select the Apple Developer Team under Signing & Capabilities.
- Confirm the bundle identifier `com.roofbrokers.crm` is available in the Apple Developer account.
- Confirm `RoofBrokers/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` contains the approved Roof Brokers logo.
- Run on a physical iPhone and verify login, lead list, lead detail, camera/photo upload, field map, call/text links, and logout.
- Test with an Owner account and a non-owner test account to verify lead isolation: Owner sees all company leads; non-owner users see only leads assigned to them.
- Archive the Release configuration.
- Upload through Xcode Organizer to App Store Connect.
- Add the build to TestFlight and invite testers.
