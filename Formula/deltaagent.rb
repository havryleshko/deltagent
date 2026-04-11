class Deltaagent < Formula
  include Language::Python::Virtualenv

  desc "Finance variance commentary agent"
  homepage "https://github.com/havryleshko/deltagent"
  url "https://github.com/havryleshko/deltagent/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "eea929e96f4363a0dc6d30b6033b2bbe2fa521bd7b6b97f811f74920dc54cd41"
  license "MIT"
  head "https://github.com/havryleshko/deltagent.git", branch: "main"

  depends_on "python@3.13"

  def install
    venv = virtualenv_create(libexec, Formula["python@3.13"].opt_bin/"python3")
    venv.pip_install_and_link buildpath
  end

  test do
    assert_match "DeltAgent CLI", shell_output("#{bin}/deltaagent --help")
  end
end
