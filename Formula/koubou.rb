class Koubou < Formula
  desc "🎯 Koubou (工房) - The artisan workshop for App Store screenshots"
  homepage "https://github.com/bitomule/koubou"
  url "https://github.com/bitomule/koubou/archive/refs/tags/v0.1.0.tar.gz"
  sha256 :no_check # Skip checksum for now, auto-generated releases
  license "MIT"
  head "https://github.com/bitomule/koubou.git", branch: "main"

  depends_on "python@3.12"

  def install
    # Install the package using pip with proper Python environment
    virtualenv_install_with_resources
    
    # Generate shell completions if supported
    # Note: This will be added once the CLI supports completion generation
  end

  def caveats
    <<~EOS
      🎯 Koubou (工房) is ready to craft beautiful screenshots!

      Quick start:
        kou create-config sample.yaml    # Create a sample configuration  
        kou generate sample.yaml         # Generate screenshots
        kou list-frames                  # List available device frames
        kou --help                       # Show all commands

      Features:
        • 🎨 100+ Device Frames (iPhone 16 Pro, iPad Air M2, Apple Watch Ultra)
        • 🌈 Professional Backgrounds (Linear, radial, conic gradients) 
        • ✨ Rich Typography (Advanced text overlays with stroke, alignment)
        • 📱 YAML-First Configuration (Elegant, declarative definitions)
        • 🚀 Batch Processing (Generate multiple screenshots efficiently)

      工房 (koubou) means "artisan's workshop" in Japanese - 
      where masters create their finest work.
    EOS
  end

  test do
    system "#{bin}/kou", "--version"
    system "#{bin}/kou", "--help"
    
    # Test creating a sample config
    system "#{bin}/kou", "create-config", "test-config.yaml"
    assert_predicate testpath/"test-config.yaml", :exist?
    
    # Test listing frames (should not fail)
    system "#{bin}/kou", "list-frames"
  end
end