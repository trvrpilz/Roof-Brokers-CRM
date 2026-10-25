import SwiftUI

@main
struct RoofBrokersApp: App {
    var body: some Scene {
        WindowGroup {
            CRMContainerView()
        }
    }
}

struct CRMContainerView: View {
    var body: some View {
        NavigationStack {
            CRMWebView(url: URL(string: "https://roof-brokers-api-staging.up.railway.app/")!)
                .ignoresSafeArea(edges: .bottom)
                .navigationTitle("Roof Brokers")
                .navigationBarTitleDisplayMode(.inline)
        }
    }
}
