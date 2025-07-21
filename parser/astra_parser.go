package main

import (
	"bufio"
	"strconv"
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"strings"
	"github.com/ProtonMail/gopenpgp/v3/crypto"
)

// AStRA Element Types
type Artifact struct {
	ID       string            `json:"id"`
	Kind     string            `json:"kind"`
	Name     string            `json:"name"`
	Version  string            `json:"version"`
	Hash     string            `json:"hash,omitempty"`
	Size     int64             `json:"size,omitempty"`
	Metadata map[string]string `json:"metadata,omitempty"`
}

type Step struct {
	ID          string            `json:"id"`
	Command     string            `json:"command"`
	Timestamp   string            `json:"timestamp"`
	Arch        string            `json:"architecture"`
	Environment map[string]string `json:"environment"`
	Consumed    []string          `json:"consumed_resources"`
	Outputs     []string          `json:"outputs"`
}

type Principal struct {
	ID       string            `json:"id"`
	Trust    string            `json:"trust_level"`
	Builder  string            `json:"builder"`
	Metadata map[string]string `json:"metadata,omitempty"`
}

type Resource struct {
	ID     string `json:"id"`
	Type   string `json:"type"`
	URI    string `json:"uri"`
	Format string `json:"format"`
	UsedBy string `json:"used_by,omitempty"`
}

// AStRA Graph container
type AstraGraph struct {
	Artifacts  []Artifact  `json:"artifacts"`
	Steps      []Step      `json:"step"`
	Principals []Principal `json:"principals"`
	Resources  []Resource  `json:"resources"`
}

func parseBuildinfo(path string) (*AstraGraph, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	graph := &AstraGraph{}

	var source, version, buildArch, buildDate, buildOrigin string
	var outputs []Artifact
	var pgpLines []string
	var keyIDs []string
	artifactInputs := []string{}
	resourceIDs := []string{}
	env := make(map[string]string)
	envSection, dependsSection, outputSection, pgpSection := false, false, false, false
	re := regexp.MustCompile(`([a-zA-Z0-9.+:~\-]+) \(= ([^\)]+)\)`)

	for scanner.Scan() {
		line := scanner.Text()

		switch {
		case strings.HasPrefix(line, "Source:"):
			source = strings.TrimSpace(strings.TrimPrefix(line, "Source:"))
		case strings.HasPrefix(line, "Version:"):
			version = strings.TrimSpace(strings.TrimPrefix(line, "Version:"))
		case strings.HasPrefix(line, "Build-Architecture:"):
			buildArch = strings.TrimSpace(strings.TrimPrefix(line, "Build-Architecture:"))
		case strings.HasPrefix(line, "Build-Date:"):
			buildDate = strings.TrimSpace(strings.TrimPrefix(line, "Build-Date:"))
		case strings.HasPrefix(line, "Build-Origin:"):
			buildOrigin = strings.TrimSpace(strings.TrimPrefix(line, "Build-Origin:"))
		case strings.HasPrefix(line, "Checksums-Sha256:"):
			outputSection = true
		case strings.HasPrefix(line, "Installed-Build-Depends:"):
			dependsSection = true
		case strings.HasPrefix(line, "Environment:"):
			envSection = true
			continue // Skip the header line
		case strings.HasPrefix(line, "-----BEGIN PGP SIGNATURE-----"):
			pgpSection = true
		case outputSection && strings.TrimSpace(line) == "":
			outputSection = false
		case dependsSection && strings.TrimSpace(line) == "":
			dependsSection = false
		case envSection && strings.TrimSpace(line) == "":
			envSection = false
		case strings.HasPrefix(line, "-----END PGP SIGNATURE-----"):
			pgpSection = false
		}

		if pgpSection {
			pgpLines = append(pgpLines, line)
		}

		if outputSection && strings.TrimSpace(line) != "" && strings.HasSuffix(line, ".deb") {
			parts := strings.Fields(line)
			if len(parts) == 3 {
				size, err := strconv.ParseInt(parts[1], 10, 64)
				if err != nil {
					size = 0
				}
				outputs = append(outputs, Artifact{
					ID:      parts[2],
					Kind:    "binary",
					Name:    parts[2],
					Hash:    parts[0],
					Size:    size,
					Version: version,
				})
			}
		} else if dependsSection && strings.TrimSpace(line) != "" {
			matches := re.FindAllStringSubmatch(line, -1)
			for _, match := range matches {
				pkg := strings.TrimSpace(match[1])
				ver := strings.TrimSpace(match[2])
				id := fmt.Sprintf("%s@%s", pkg, ver)
				uri := fmt.Sprintf("https://deb.debian.org/debian/pool/main/%s/%s_%s.deb",
					strings.ToLower(string(pkg[0])), pkg, ver)

				if !contains(resourceIDs, id) {
					resourceIDs = append(resourceIDs, id)
					artifactInputs = append(artifactInputs, id)
					graph.Resources = append(graph.Resources, Resource{
						ID:     id,
						Type:   "build-dependency",
						URI:    uri,
						Format: "deb",
						UsedBy: buildOrigin,
					})
				}
			}
		} else if envSection {
			trimmed := strings.TrimSpace(line)
			// Exit early if next section starts or line is empty
			if trimmed == "" || strings.HasPrefix(trimmed, "-----BEGIN") || strings.Contains(trimmed, ":") {
				envSection = false
				continue
			}

			// Only parse lines that look like env vars (contain =)
			if strings.Contains(trimmed, "=") {
				parts := strings.SplitN(trimmed, "=", 2)
				key := strings.TrimSpace(parts[0])
				val := strings.Trim(parts[1], `"`)
				if key != "" {
					env[key] = val
				}
			}
		}
	}

	stepID := fmt.Sprintf("build-%s@%s", source, version)
	outputIDs := []string{}
	for _, a := range outputs {
		outputIDs = append(outputIDs, a.ID)
		graph.Artifacts = append(graph.Artifacts, a)
	}

	upstreamVersion := strings.SplitN(version, "-", 2)[0]
	tarball := fmt.Sprintf("%s_%s.orig.tar.xz", source, upstreamVersion)
	tarballURI := fmt.Sprintf("https://deb.debian.org/debian/pool/main/%s/%s/%s",
		strings.ToLower(string(source[0])), source, tarball)

	graph.Resources = append(graph.Resources, Resource{
		ID:     tarball,
		Type:   "tarball",
		URI:    tarballURI,
		Format: "orig.tar.xz",
		UsedBy: buildOrigin,
	})
	resourceIDs = append(resourceIDs, tarball)

	graph.Steps = append(graph.Steps, Step{
		ID:          stepID,
		Command:     "dpkg-buildpackage",
		Timestamp:   buildDate,
		Arch:        buildArch,
		Environment: env,
		Consumed:   resourceIDs,
		Outputs:     outputIDs,
	})

	if len(pgpLines) > 0 {
		pgpText := strings.Join(pgpLines, "\n")
		pgpMsg, err := crypto.NewPGPMessageFromArmored(pgpText)
		if err == nil {
			if ids, ok := pgpMsg.HexSignatureKeyIDs(); ok && len(ids) > 0 {
				keyIDs = ids
			}
		}
	}

	principal := Principal{
		ID:      buildOrigin,
		Trust:   "signed",
		Builder: "Debian Build Infrastructure",
	}
	if len(keyIDs) > 0 {
		principal.Metadata = map[string]string{
			"pgp_key_id": keyIDs[0],
		}
	}
	graph.Principals = append(graph.Principals, principal)

	return graph, nil
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: astra-parser <buildinfo-file>")
		return
	}

	inputPath := os.Args[1]
	graph, err := parseBuildinfo(inputPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	output, err := json.MarshalIndent(graph, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "JSON Error: %v\n", err)
		os.Exit(1)
	}

	inputParts := strings.Split(inputPath, "/")
	inputFile := inputParts[len(inputParts)-1]
	outputFile := strings.TrimSuffix(inputFile, ".txt") + ".json"
	outPath := "output/" + outputFile

	err = os.WriteFile(outPath, output, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "File write error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Graph saved to %s\n", outPath)
}
