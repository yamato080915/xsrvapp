<?php
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}

const SUPABASE_HEALTHCHECK_URL = 'https://ohzhrcymowwfvbfxtkcj.supabase.co/rest/v1/rpc/team_shuffle_healthcheck';
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_v9RCRhsUbAyB_lCvkCq2Zg_ioCD-2qS';

function fail(string $message): never
{
    fwrite(STDERR, '[supabase-keepalive] ' . $message . PHP_EOL);
    exit(1);
}

function requestWithCurl(): array
{
    $handle = curl_init(SUPABASE_HEALTHCHECK_URL);
    if ($handle === false) {
        fail('curl_init failed.');
    }

    curl_setopt_array($handle, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => '{}',
        CURLOPT_HTTPHEADER => [
            'apikey: ' . SUPABASE_PUBLISHABLE_KEY,
            'Content-Type: application/json',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 20,
    ]);

    $body = curl_exec($handle);
    if ($body === false) {
        $error = curl_error($handle);
        curl_close($handle);
        fail('Request failed: ' . $error);
    }

    $status = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
    curl_close($handle);

    return [$status, $body];
}

function requestWithStream(): array
{
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => implode("\r\n", [
                'apikey: ' . SUPABASE_PUBLISHABLE_KEY,
                'Content-Type: application/json',
            ]),
            'content' => '{}',
            'timeout' => 20,
            'ignore_errors' => true,
        ],
    ]);

    $body = @file_get_contents(SUPABASE_HEALTHCHECK_URL, false, $context);
    if ($body === false) {
        fail('HTTP request failed.');
    }

    $status = 0;
    foreach ($http_response_header ?? [] as $header) {
        if (preg_match('/^HTTP\/\S+\s+(\d{3})\b/', $header, $matches) === 1) {
            $status = (int) $matches[1];
        }
    }

    return [$status, $body];
}

[$status, $body] = function_exists('curl_init')
    ? requestWithCurl()
    : requestWithStream();

if ($status < 200 || $status >= 300) {
    fail('Unexpected HTTP status ' . $status . ': ' . $body);
}

$payload = json_decode($body, true);
if (!is_array($payload) || ($payload['ok'] ?? false) !== true) {
    fail('Unexpected response: ' . $body);
}
