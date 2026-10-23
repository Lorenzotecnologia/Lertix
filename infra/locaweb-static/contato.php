<?php
// Ajuste antes de publicar: o remetente deve ser uma caixa de e-mail do domínio hospedado na Locaweb.
const MAIL_TO = 'contato@lertrix.com';
const MAIL_FROM = 'contato@lertrix.com';

header('Content-Type: text/html; charset=utf-8');

function clean(string $value, int $max): string
{
    $value = trim(str_replace(["\r", "\0"], '', $value));
    return mb_substr($value, 0, $max);
}

function page(string $title, string $text, int $status = 200): void
{
    http_response_code($status);
    $title = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $text = htmlspecialchars($text, ENT_QUOTES, 'UTF-8');
    echo "<!doctype html><html lang=\"pt-br\"><head><meta charset=\"utf-8\">"
        . "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        . "<title>{$title} — Lertrix Edições</title>"
        . "<link rel=\"stylesheet\" href=\"/static/css/storefront.css\"></head>"
        . "<body><main class=\"section-wrap\" style=\"padding:4rem 1rem;text-align:center\">"
        . "<h1>{$title}</h1><p>{$text}</p>"
        . "<p><a class=\"button\" href=\"/#contato\">Voltar ao site</a></p></main></body></html>";
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /#contato', true, 303);
    exit;
}

// Campo isca: bots o preenchem, pessoas não o veem.
if (!empty($_POST['website'])) {
    page('Envio inválido', 'Não foi possível enviar a mensagem.', 400);
}

$name = clean((string)($_POST['name'] ?? ''), 120);
$email = clean((string)($_POST['email'] ?? ''), 254);
$subject = clean((string)($_POST['subject'] ?? ''), 150);
$message = clean((string)($_POST['message'] ?? ''), 5000);

if ($name === '' || $message === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    page('Dados incompletos', 'Informe nome, um e-mail válido e a mensagem.', 400);
}

$subject = preg_replace('/[\r\n]+/', ' ', $subject);
$headers = [
    'From: Site Lertrix <' . MAIL_FROM . '>',
    'Reply-To: ' . $email,
    'Content-Type: text/plain; charset=UTF-8',
];
$body = "De: {$name} <{$email}>\n\n{$message}";
$title = '[Site Lertrix] ' . ($subject !== '' ? $subject : 'Nova mensagem');
$sent = mail(MAIL_TO, '=?UTF-8?B?' . base64_encode($title) . '?=', $body, implode("\r\n", $headers), '-f' . MAIL_FROM);

if (!$sent) {
    page('Não foi possível enviar', 'Tente novamente em instantes ou fale conosco pelo WhatsApp.', 500);
}
page('Mensagem enviada!', 'Responderemos em breve.');
