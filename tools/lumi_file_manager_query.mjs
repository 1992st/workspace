#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const val = argv[i + 1];
    if (!key.startsWith('--')) continue;
    const k = key.slice(2);
    if (val && !val.startsWith('--')) {
      out[k] = val;
      i += 1;
    } else {
      out[k] = 'true';
    }
  }
  return out;
}

function extractJsonSpec(md) {
  const match = md.match(/```json\n([\s\S]*?)\n```/);
  if (!match) throw new Error('RoutingSpec JSON block not found in config');
  return JSON.parse(match[1]);
}

function normalizeText(s) {
  return (s || '').toLowerCase().trim();
}

function detectByAlias(query, map) {
  const q = normalizeText(query);
  let best = '';
  let bestLen = 0;
  for (const [target, aliases] of Object.entries(map || {})) {
    for (const rawAlias of aliases) {
      const alias = normalizeText(rawAlias);
      if (!alias) continue;
      if (q.includes(alias) && alias.length > bestLen) {
        best = target;
        bestLen = alias.length;
      }
    }
  }
  return best;
}

function buildPaths(template, docType, platform, stages) {
  const base = template
    .replaceAll('{doc_type}', docType)
    .replaceAll('{platform}', platform);
  const out = {};
  for (const s of stages) out[s] = path.posix.join(base, s);
  return out;
}

function resolveRoute(spec, docType, platform) {
  const byType = spec.routes?.[docType];
  if (!byType) return '';
  return byType[platform] || byType.internal || '';
}

function listCandidates(spec) {
  return {
    doc_types: spec.supported?.doc_types || [],
    platforms: spec.supported?.platforms || [],
  };
}

function main() {
  try {
    const args = parseArgs(process.argv);
    const intent = args.intent || 'locate_new_doc';
    const configPath = args.config || 'skills/lumi_file_manager/config.md';
    const query = args.query || '';

    const md = fs.readFileSync(configPath, 'utf8');
    const spec = extractJsonSpec(md);

    const docTypeExplicit = args.doc_type || args.doc_type_hint || '';
    const platformExplicit = args.platform || args.platform_hint || '';

    const detectedDocType = detectByAlias(query, spec.aliases?.doc_type);
    const detectedPlatform = detectByAlias(query, spec.aliases?.platform);

    const hasDocTypeSignal = Boolean(docTypeExplicit || detectedDocType);
    const docType = docTypeExplicit || detectedDocType || spec.defaults?.doc_type || '';
    const platformDefault = spec.defaults?.platform_by_type?.[docType] || spec.defaults?.platform || '';
    const platform = platformExplicit || detectedPlatform || platformDefault;

    const supportedTypes = new Set(spec.supported?.doc_types || []);
    const supportedPlatforms = new Set(spec.supported?.platforms || []);

    if (!hasDocTypeSignal) {
      const res = {
        status: 'confirm_required',
        confidence: 0.45,
        reasoning: 'doc_type cannot be inferred from query or hints',
        candidates: listCandidates(spec),
      };
      console.log(JSON.stringify(res, null, 2));
      return;
    }

    if (!docType || !supportedTypes.has(docType)) {
      const res = {
        status: 'confirm_required',
        confidence: 0.45,
        reasoning: 'doc_type is missing or unsupported',
        candidates: listCandidates(spec),
      };
      console.log(JSON.stringify(res, null, 2));
      return;
    }

    if (!platform || !supportedPlatforms.has(platform)) {
      const res = {
        status: 'confirm_required',
        confidence: 0.55,
        resolved_doc_type: docType,
        reasoning: 'platform is missing or unsupported',
        candidates: listCandidates(spec),
      };
      console.log(JSON.stringify(res, null, 2));
      return;
    }

    const routeTemplate = resolveRoute(spec, docType, platform);
    if (!routeTemplate) {
      const res = {
        status: 'failed',
        confidence: 0,
        resolved_doc_type: docType,
        resolved_platform: platform,
        reasoning: 'route template not found for doc_type/platform',
        candidates: listCandidates(spec),
      };
      console.log(JSON.stringify(res, null, 2));
      process.exitCode = 1;
      return;
    }

    const targetPaths = buildPaths(routeTemplate, docType, platform, spec.stages || ['working', 'publish']);

    if (intent === 'list_paths' || intent === 'locate_new_doc') {
      const res = {
        status: 'ok',
        confidence: 0.9,
        resolved_doc_type: docType,
        resolved_platform: platform,
        target_paths: targetPaths,
        reasoning: 'resolved via explicit hints + alias mapping + defaults',
      };
      console.log(JSON.stringify(res, null, 2));
      return;
    }

    if (intent === 'validate_path') {
      const filePath = args.file_path || '';
      const normalized = filePath.replaceAll('\\\\', '/');
      const valid = Object.values(targetPaths).some((p) => normalized.includes(`${p}/`) || normalized === p);
      const res = {
        status: valid ? 'ok' : 'confirm_required',
        confidence: valid ? 0.95 : 0.6,
        resolved_doc_type: docType,
        resolved_platform: platform,
        target_paths: targetPaths,
        file_path: filePath,
        valid,
        reasoning: valid ? 'file path matches configured route' : 'file path is outside configured route',
      };
      console.log(JSON.stringify(res, null, 2));
      return;
    }

    console.log(JSON.stringify({
      status: 'failed',
      confidence: 0,
      reasoning: `unsupported intent: ${intent}`,
    }, null, 2));
    process.exitCode = 1;
  } catch (err) {
    console.log(JSON.stringify({
      status: 'failed',
      confidence: 0,
      reasoning: err instanceof Error ? err.message : String(err),
    }, null, 2));
    process.exitCode = 1;
  }
}

main();
