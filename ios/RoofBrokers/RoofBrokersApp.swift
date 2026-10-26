import SwiftUI

@main
struct RoofBrokersApp: App {
    var body: some Scene {
        WindowGroup {
            CRMWebView()
                .ignoresSafeArea(.container, edges: .bottom)
        }
    }
}
